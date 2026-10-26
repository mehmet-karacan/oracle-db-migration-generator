"""Explicit browser handoff for an approved existing job; no borrowed browser auth.

Bindings are server-owned files, never request input. The CLI links metadata only
after an operator has observed the authenticated Jenkins result. It is not an
automatic Jenkins executor or proof of delivery to a mail inbox.
"""
from datetime import datetime,timezone
import json
import math
import os
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from ..config.loader import validate_document
from ..model.serialization import digest


def spec_fingerprint(spec):
    profile={k:v for k,v in spec['profile'].items() if k not in {'id','revision','updated_at','name','mapping_id','mapping_revision'}}
    for key in ('object_types','excluded_object_types','target_ids'):profile[key]=sorted(profile[key])
    profile['source']={**profile['source'],'schemas':sorted(profile['source']['schemas'])}
    mappings=profile.pop('target_mappings',None)
    if mappings is not None:
        normalized={key:sorted(values,key=lambda m:(m['source_schema'],m['target_schema'])) for key,values in mappings.items()}
        default=[{'source_schema':s,'target_schema':s} for s in profile['source']['schemas']]
        if normalized!={key:default for key in profile['target_ids']}:profile['target_mappings']=normalized
    settings={k:v for k,v in spec['settings'].items() if k not in {'id','revision','updated_at','project_id'}}
    # Connection revision pins the encrypted credential version as well as its endpoint.
    return digest({'profile':profile,'settings':settings,'connections':spec['connections']})


def approved_handoff(spec,*,root=None):
    path=os.environ.get('ODMG_UI_JENKINS_BINDINGS')
    if not path and root is not None:
        saved=Path(root)/'jenkins-bindings.json'
        if saved.is_file():path=saved
    if not path:return None
    records=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    scoped=[b for b in records if b['project_id']==spec['project']['id']]
    if not scoped:raise ValueError('JENKINS_PROFILE_NOT_CONFIGURED')
    matching=[b for b in scoped if b['profile_id']==spec['profile']['id'] and b['fingerprint']==spec_fingerprint(spec)]
    if len(matching)!=1:raise ValueError('JENKINS_PROFILE_NOT_CONFIGURED')
    b=matching[0];url=b['job_url'];parsed=urlsplit(url)
    if (parsed.scheme not in {'https','http'} or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or not url.endswith('/')
            or set(b['target_map'])!=set(spec['profile']['target_ids'])
            or spec['profile']['source']['kind']!='GIT'
            or spec['profile']['source']['schemas']!=[b['schema_scope']]):
        raise ValueError('JENKINS_BINDING_INVALID')
    return {**b,'mode':'BROWSER_HANDOFF','launch_url':url+'build?delay=0sec',
            'parameters':{'SCHEMA_SCOPE':b['schema_scope'],'RUN_MODE':'COMPARE'}}


def _time(value):
    parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    if parsed.tzinfo is None:raise ValueError('RESULT_TIMEZONE_REQUIRED')
    return parsed


def _run_id_matches(value,number):
    if value==f'build-{number}':return True
    try:return str(UUID(value))==value
    except (ValueError,TypeError,AttributeError):return False


def link_completed_run(store,id,document,*,performance=None):
    """Local operator boundary. Call only with metadata read from the bound job."""
    run=store.run(id);external=run.get('external',{})
    if external.get('mode')!='BROWSER_HANDOFF':raise ValueError('HANDOFF_REQUIRED')
    validate_document(document,'run.schema.json')
    receipt=digest({'run':document,'performance':performance})
    if external.get('result_digest'):
        if external['result_digest']!=receipt:raise ValueError('RESULT_ALREADY_LINKED')
        return run
    if run['status']!='AWAITING_JENKINS':raise ValueError('HANDOFF_NOT_PENDING')
    number=document.get('build_number')
    target_ids=set(external['target_map'].values())
    start=_time(document['started_at']);end=_time(document['finished_at'])
    if (document.get('synthetic',False) or not document.get('source_commit') or 'source_origin' in document
            or not isinstance(number,int) or number<1 or not _run_id_matches(document['run_id'],number)
            or document.get('build_url')!=external['job_url']+f'{number}/'
            or start<_time(run['created_at']) or end<start or end>datetime.now(timezone.utc)
            or {t['id'] for t in document['targets']}!=target_ids or len(document['targets'])!=len(target_ids)
            or any(t['captured_at'] and not start<=_time(t['captured_at'])<=end for t in document['targets'])):
        raise ValueError('JENKINS_RESULT_MISMATCH')
    timing={}
    if performance is not None:
        seconds=performance.get('total_seconds')
        if (performance.get('schema_version')!='source-preparation-performance/1.0'
                or performance.get('source_commit')!=document['source_commit']
                or isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds)
                or not 0<=seconds<=(end-start).total_seconds()
                or not isinstance(performance.get('cache_status'),str)):
            raise ValueError('JENKINS_TIMING_MISMATCH')
        timing={'source_performance':{'seconds':seconds,'cache_status':performance['cache_status'],'source_kind':'GIT'}}
    external={**external,'build_url':document['build_url'],
              'report_url':document['build_url']+f'artifact/output/runs/build-{number}/index.html',
              'verification':'BROWSER_OBSERVED','result_digest':receipt,'build_number':number,
              'canonical_run_id':document['run_id']}
    return store.link_external_run(id,status=document['status'],stage='FINISHED',started_at=document['started_at'],
        finished_at=document['finished_at'],targets=document['targets'],source_commit=document['source_commit'],
        external=external,events=[{'stage':'FINISHED','at':document['finished_at']}],**timing)
