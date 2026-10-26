"""Read-only object explorer over recorded canonical differences, not a new comparator."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

from ..model.serialization import digest
from .result_models import ResultView,metadata_path
from .store import now


def project_plan(plan):
    def value(path,item):
        omitted=not metadata_path(path)
        return {'state':item['state'],'value':None if omitted else item['value'],'omitted':omitted}
    differences=[]
    for row in plan['differences']:
        path=row['property_path']
        if not path.startswith('/'):path='/'+path.replace('.','/')
        differences.append({k:row[k] for k in ('id','object_key','kind','evidence_ids')}|{
            'property_path':path,'source':value(path,row['after']),'target':value(path,row['before'])})
    operations=[{k:op.get(k,[]) for k in ('id','object','kind','decision','reason_tr','change_ids','evidence_ids','depends_on')}|
                {'sql_path':op['sql']['path'] if op.get('sql') else None} for op in plan['operations']]
    return ResultView.model_validate({'schema_version':'comparison-view/1.0','plan_id':plan['plan_id'],
        'source_commit':plan['source']['commit_sha'],'target_id':plan['target']['id'],'synthetic':plan['synthetic'],
        'scope':plan['scope'],'counts':plan['counts'],'differences':differences,'operations':operations}).model_dump()


def target_record(run,target_id):
    if target_id not in run['spec']['profile']['target_ids']:raise KeyError('TARGET_NOT_FOUND')
    external_id=(run.get('external') or {}).get('target_map',{}).get(target_id,target_id)
    return next((t for t in run['targets'] if t['id']==external_id),None),external_id


def _matches(run,target_id,view):
    target,external_id=target_record(run,target_id)
    if (not target or target.get('plan_id')!=view['plan_id'] or external_id!=view['target_id']
            or run.get('source_commit')!=view['source_commit']
            or run.get('external') and view['synthetic']):raise ValueError('RESULT_VIEW_MISMATCH')


def import_view(store,id,target_id,document):
    view=ResultView.model_validate(document).model_dump();checksum=digest(view)
    with store.transaction() as db:
        row=db.execute('SELECT document FROM runs WHERE id=?',(id,)).fetchone()
        if not row:raise KeyError('RUN_NOT_FOUND')
        run=json.loads(row[0]);_matches(run,target_id,view)
        if run['status'] not in {'COMPLETE','PARTIAL','FAILED'}:raise ValueError('RESULT_NOT_FINISHED')
        previous=db.execute('SELECT sha256 FROM comparison_views WHERE run_id=? AND target_id=?',(id,target_id)).fetchone()
        if previous:
            if previous[0]!=checksum:raise ValueError('RESULT_VIEW_IMMUTABLE')
        else:
            db.execute('INSERT INTO comparison_views VALUES(?,?,?,?)',(id,target_id,checksum,json.dumps(view,ensure_ascii=False)))
            db.execute('INSERT INTO audit(at,actor,action,record_id) VALUES(?,?,?,?)',(now(),'shared','run.import_result_view',id))
    return {'plan_id':view['plan_id'],'objects':len(index_view(view)['objects']),'differences':len(view['differences']),'sha256':checksum}


@lru_cache(maxsize=4)
def _local_view(path,mtime,size):
    if size>64*1024*1024:raise ValueError('RESULT_TOO_LARGE')
    return project_plan(json.loads(Path(path).read_bytes()))


@lru_cache(maxsize=4)
def _saved_view(checksum,document):
    view=ResultView.model_validate_json(document).model_dump()
    if digest(view)!=checksum:raise ValueError('RESULT_VIEW_HASH_MISMATCH')
    return view


def load_view(store,run,target_id):
    target,external_id=target_record(run,target_id)
    if not target or not target.get('plan_id'):return None
    with store.transaction() as db:
        saved=db.execute('SELECT sha256,document FROM comparison_views WHERE run_id=? AND target_id=?',(run['id'],target_id)).fetchone()
    if saved:view=_saved_view(*saved)
    else:
        path=store.root/'runs'/run['id']/'targets'/external_id/'plan.json'
        if not path.is_file():return None
        stat=path.stat();view=_local_view(str(path),stat.st_mtime_ns,stat.st_size)
    _matches(run,target_id,view)
    return view


def object_key(identity):
    values=[identity['profile_id'],identity['owner'],identity['object_type'],identity['name'],identity['parent_key']]
    return hashlib.sha256(json.dumps(values,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def section(path):
    group=path.strip('/').split('/')[0]
    return {'columns':'columns','constraints':'constraints','index':'indexes'}.get(group,'other')


def index_view(view):
    objects={};by_change={r['id']:r for r in view['differences']}
    for op in view['operations']:
        identity=op['object'];key=object_key(identity)
        obj=objects.setdefault(key,{'key':key,**identity,'differences':[],'operations':[]})
        if identity.get('display_name'):obj['display_name']=identity['display_name']
        obj['operations'].append(op)
    for row in view['differences']:
        key=row['object_key']
        if key not in objects:
            objects[key]={'key':key,'owner':'','name':'Kimliği çözülemeyen nesne '+key[:8],'object_type':'UNKNOWN','differences':[],'operations':[]}
        objects[key]['differences'].append(row)
    # Related operations are resolved by canonical change IDs; no object-name guesses.
    for op in view['operations']:
        for key in {by_change[c]['object_key'] for c in op['change_ids']}:
            if op not in objects[key]['operations']:objects[key]['operations'].append(op)
    return {'objects':objects}


def object_page(view,*,page,size,search,object_type,difference_kind=""):
    objects=index_view(view)['objects'];needle=search.casefold()
    unknown=sum(row['kind']=='UNKNOWN' for row in view['differences'])
    rows=[obj for obj in objects.values() if (not object_type or obj['object_type']==object_type)
          and (not needle or needle in (obj['owner']+'.'+obj['name']+' '+(obj.get('display_name') or '')).casefold())
          and (not difference_kind or any(r['kind']==difference_kind for r in obj['differences']))]
    rows.sort(key=lambda obj:(obj['owner'],obj.get('display_name') or obj['name'],obj['object_type'],obj['key']))
    return {'available':True,'plan_id':view['plan_id'],'scope':view['scope'],'counts':view['counts'],
        'total':len(rows),'total_objects':len(objects),'page':page,'size':size,'unknown_count':unknown,
        'observed_difference_count':len(view['differences'])-unknown,
        'rows':[{k:o[k] for k in ('key','owner','name','object_type')}|{'difference_count':len(o['differences']),
                'display_name':o.get('display_name'),
                'difference_kinds':sorted({r['kind'] for r in o['differences']}),
                'operation_count':len(o['operations']),'decisions':sorted({op['decision'] for op in o['operations']})}
                for o in rows[(page-1)*size:page*size]]}


def _sql_url(run,target_id,path):
    if not path:return None
    _,external_id=target_record(run,target_id)
    external=run.get('external')
    if external:
        return external['build_url']+f'artifact/output/runs/build-{external.get("build_number") or external["build_url"].rstrip("/").split("/")[-1]}/targets/{quote(external_id,safe="")}/{quote(path,safe="/")}/*view*/'
    if run.get('executor')=='JENKINS':
        build_url=run.get('archive_build_url')
        if not build_url:return None
        number=build_url.rstrip('/').rsplit('/',1)[-1]
        if not number.isdigit():return None
        return build_url+f'artifact/output/runs/build-{number}/targets/{quote(external_id,safe="")}/{quote(path,safe="/")}/*view*/'
    return f'/api/runs/{run["id"]}/artifacts/targets/{quote(external_id,safe="")}/{quote(path,safe="/")}?project_id={quote(run.get("project_id",run["spec"]["profile"].get("project_id","")),safe="")}'


def object_detail(view,run,target_id,key,*,category,page,size,operation_page,grouped=False,operation_group=""):
    obj=index_view(view)['objects'].get(key)
    if obj is None:raise KeyError('OBJECT_NOT_FOUND')
    rows=[r for r in obj['differences'] if category=='all' or section(r['property_path'])==category]
    counts={k:sum(section(r['property_path'])==k for r in obj['differences']) for k in ('columns','constraints','indexes','other')}
    from .structure import structure_groups,structure_summary
    groups=structure_groups(obj);filtered=[g for g in groups if category=='all' or g['section']==category]
    operations=obj['operations']
    if operation_group:
        group=next((g for g in groups if g['id']==operation_group),None)
        if group is None:raise KeyError('OBJECT_GROUP_NOT_FOUND')
        operations=[op for op in operations if op['id'] in group['operation_ids']]
    op_rows=operations[(operation_page-1)*10:operation_page*10]
    return {'key':key,'owner':obj['owner'],'name':obj['name'],'object_type':obj['object_type'],
        'display_name':obj.get('display_name'),
        'scope':view['scope'],'plan_id':view['plan_id'],'sections':counts,'total':len(rows),'rows':[] if grouped else rows[(page-1)*size:page*size],
        'summary':structure_summary(obj,groups),'group_total':len(filtered),'group_sections':{k:sum(g['section']==k for g in groups) for k in counts},
        'groups':filtered[(page-1)*size:page*size] if grouped else [],'object_operation_total':len(obj['operations']),
        'operation_total':len(operations),'operations':[{**op,'sql_url':_sql_url(run,target_id,op['sql_path'])} for op in op_rows],
        'page':page,'size':size,'operation_page':operation_page,'recorded_differences_only':True}
