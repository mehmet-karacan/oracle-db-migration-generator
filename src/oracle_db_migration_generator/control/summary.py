"""SQL-free summary from recorded plans and operator-observed inventory receipts."""
from collections import Counter
import hashlib
import json
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,field_validator
from .models import OBJECT_TYPES
from .results import load_view,target_record
from ..model.serialization import digest


class Side(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    by_schema:dict[str,dict[str,int]]
    inventory:Literal['COMPLETE','PARTIAL','UNAVAILABLE']
    excluded:int=Field(ge=0)

    @field_validator('by_schema')
    @classmethod
    def counters(cls,value):
        if len(value)>20 or any(len(owner)>128 or not owner or set(counts)-set(OBJECT_TYPES)
            or any(type(n) is not int or n<0 for n in counts.values()) for owner,counts in value.items()):
            raise ValueError('SCAN_SUMMARY_INVALID')
        return value


class Scan(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    schema_version:Literal['scan-summary/1.0']
    plan_id:str=Field(pattern='^[a-f0-9]{64}$')
    source_digest:str=Field(pattern='^[a-f0-9]{64}$')
    target_digest:str=Field(pattern='^[a-f0-9]{64}$')
    target_id:str
    source:Side
    target:Side


def checked_scan(run,target_id,document):
    scan=Scan.model_validate(document).model_dump()
    target,external_id=target_record(run,target_id)
    profile=run['spec']['profile']
    pairs=(profile.get('target_mappings') or {}).get(target_id)
    owners={p['source_schema'] for p in pairs} if pairs else set(profile['source']['schemas'])
    if (not target or target.get('plan_id')!=scan['plan_id'] or scan['target_id']!=external_id
            or set(scan['source']['by_schema'])!=owners or set(scan['target']['by_schema'])!=owners):
        raise ValueError('SCAN_SUMMARY_SCOPE_MISMATCH')
    return scan


def import_scan(store,id,target_id,raw,manifest):
    if len(raw)>256*1024:raise ValueError('SCAN_SUMMARY_TOO_LARGE')
    run=store.run(id);scan=checked_scan(run,target_id,json.loads(raw))
    rows=[r for r in manifest.get('files',[]) if r.get('path')=='scan-summary.json']
    if (len(rows)!=1 or rows[0].get('bytes')!=len(raw) or rows[0].get('sha256')!=hashlib.sha256(raw).hexdigest()
            or manifest.get('plan_id')!=scan['plan_id']):raise ValueError('SCAN_SUMMARY_INTEGRITY_MISMATCH')
    if not load_view(store,run,target_id):raise ValueError('RESULT_VIEW_UNAVAILABLE')
    checksum=digest(scan)
    with store.transaction() as db:
        prior=db.execute('SELECT sha256 FROM scan_views WHERE run_id=? AND target_id=?',(id,target_id)).fetchone()
        if prior and prior[0]!=checksum:raise ValueError('SCAN_SUMMARY_IMMUTABLE')
        if not prior:db.execute('INSERT INTO scan_views VALUES(?,?,?,?)',(id,target_id,checksum,json.dumps(scan)))
    return {'plan_id':scan['plan_id'],'sha256':checksum}


def run_summary(store,run):
    counts=Counter();unknown=0;complete=True;sources={};inventory_complete=True
    expected=set(run['spec']['profile']['source']['schemas']);targets=[]
    for id in run['spec']['profile']['target_ids']:
        view=load_view(store,run,id)
        targets.append({'id':id,'counts':view['counts'] if view else None})
        if view:
            counts.update(view['counts']);unknown+=sum(d['kind']=='UNKNOWN' for d in view['differences'])
        else:complete=False
        with store.transaction() as db:
            saved=db.execute('SELECT sha256,document FROM scan_views WHERE run_id=? AND target_id=?',(run['id'],id)).fetchone()
        scan=None
        if saved:
            scan=checked_scan(run,id,json.loads(saved[1]))
            if digest(scan)!=saved[0]:raise ValueError('SCAN_SUMMARY_INTEGRITY_MISMATCH')
        elif not run.get('external'):
            _,external_id=target_record(run,id)
            folder=store.root/'runs'/run['id']/'targets'/external_id
            path=folder/'scan-summary.json'
            if path.is_file():
                from ..reporting.inventory import validate_scan_summary
                raw=path.read_bytes();manifest=json.loads((folder/'bundle-manifest.json').read_bytes())
                rows=[r for r in manifest['files'] if r['path']=='scan-summary.json']
                if len(rows)!=1 or rows[0]['bytes']!=len(raw) or rows[0]['sha256']!=hashlib.sha256(raw).hexdigest():raise ValueError('SCAN_SUMMARY_INTEGRITY_MISMATCH')
                scan=checked_scan(run,id,json.loads(raw))
                validate_scan_summary(scan,json.loads((folder/'plan.json').read_bytes()))
        if scan and scan['source']['inventory']!='UNAVAILABLE':
            inventory_complete &= scan['source']['inventory']=='COMPLETE'
            for owner,values in scan['source']['by_schema'].items():
                record=(scan['source_digest'],values)
                if owner in sources and sources[owner]!=record:raise ValueError('SCAN_SUMMARY_SOURCE_CONFLICT')
                sources[owner]=record
    types=Counter()
    for _,values in sources.values():types.update({k:v for k,v in values.items() if k not in {'COMMENT','GRANT'}})
    return {'source_total':sum(types.values()) if sources else None,'source_types':dict(types),
        'source_inventory':'COMPLETE' if sources and expected<=sources.keys() and inventory_complete else 'PARTIAL' if sources else 'UNAVAILABLE',
        'counts':dict(counts) if complete else None,'verified_difference_count':counts['observed_differences']-unknown if complete else None,'unknown_count':unknown if complete else None,'targets':targets}
