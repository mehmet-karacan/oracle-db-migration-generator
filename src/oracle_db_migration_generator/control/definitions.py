"""Private original DDL reads, bound to an authorized run and canonical object."""
import hashlib
from ..config.loader import read_json,validate_document
from ..model.serialization import digest
from ..model.snapshot_io import safe_path
from .results import index_view,object_key,target_record
from .structure import presence_status,pointer_parts

MAX_SNAPSHOT_BYTES=64*1024*1024
MAX_DEFINITION_BYTES=2*1024*1024


def checked_document(path):
    if path.stat().st_size>MAX_SNAPSHOT_BYTES:raise ValueError('DEFINITION_TOO_LARGE')
    return read_json(path)


def snapshot_digest(document):
    # snapshot/1.0 semantic fields, identical to SchemaSnapshot.semantic_digest.
    return digest({'profile_id':document['profile_id'],'schemas':document['schemas'],'coverage':document['coverage'],
        'capabilities':{k:{'state':v['state'],'value':v['value']} for k,v in document['capabilities'].items()},
        'objects':[{'key':o['object_key'],'coverage':o['coverage'],
                    'properties':{k:{'state':v['state'],'value':v['value']} for k,v in o['properties'].items()}}
                   for o in sorted(document['objects'],key=lambda item:item['object_key'])]})


def read_side(root,relative,side,key,plan,absence):
    try:
        path=safe_path(root,relative)
        if not path.is_file():return {'state':'ABSENT' if absence else 'UNAVAILABLE'}
        document=checked_document(path);validate_document(document,'snapshot.schema.json')
        expected=plan['source']['ddl_digest'] if side=='SOURCE' else plan['target_snapshot_digest']
        if (document['side']!=side or snapshot_digest(document)!=expected or document['semantic_digest']!=expected
                or document['profile_id']!=plan['source']['profile_id']
                or side=='SOURCE' and document['source_commit']!=plan['source']['commit_sha']
                or side=='TARGET' and document['target_id']!=plan['target']['id']):raise ValueError('DEFINITION_INTEGRITY')
        obj=next((o for o in document['objects'] if o['object_key']==key),None)
        if obj is None:return {'state':'ABSENT' if absence else 'UNAVAILABLE'}
        if object_key(obj['identity'])!=key:raise ValueError('DEFINITION_INTEGRITY')
        if not obj['ddl_path'] or not obj['ddl_sha256']:return {'state':'UNAVAILABLE'}
        blob=safe_path(path.parent,obj['ddl_path'])
        # The SQL path must remain under this run as well as its snapshot folder.
        if not blob.resolve().is_relative_to(root.resolve()):raise ValueError('DEFINITION_INTEGRITY')
        if not blob.is_file():return {'state':'UNAVAILABLE'}
        if blob.stat().st_size>MAX_SNAPSHOT_BYTES:return {'state':'TOO_LARGE'}
        payload=blob.read_bytes();full_hash=hashlib.sha256(payload).hexdigest()
        evidence=[e for e in document['evidence'] if e['id'] in obj['evidence_ids'] and e['path']==obj['ddl_path']]
        if any(e.get('sha256') and e['sha256']!=full_hash for e in evidence):raise ValueError('DEFINITION_INTEGRITY')
        if full_hash!=obj['ddl_sha256']:
            candidate=None
            for e in evidence:
                a,b=e.get('start_byte'),e.get('end_byte')
                if isinstance(a,int) and isinstance(b,int) and 0<=a<b<=len(payload):
                    part=payload[a:b]
                    if hashlib.sha256(part).hexdigest()==obj['ddl_sha256']:candidate=part;break
            if candidate is None:raise ValueError('DEFINITION_INTEGRITY')
            payload=candidate
        if len(payload)>MAX_DEFINITION_BYTES or payload.count(b'\n')>20000:return {'state':'TOO_LARGE'}
        return {'state':'AVAILABLE','text':payload.decode('utf-8')}
    except FileNotFoundError:return {'state':'UNAVAILABLE'}
    except (ValueError,KeyError,TypeError,UnicodeError):return {'state':'INTEGRITY_ERROR'}
    except OSError:return {'state':'UNAVAILABLE'}


def object_definitions(store,run,target_id,key,view):
    obj=index_view(view)['objects'].get(key)
    if obj is None:raise KeyError('OBJECT_NOT_FOUND')
    if run.get('external') or run.get('executor')=='JENKINS':
        return {'source':{'state':'ARCHIVED'},'target':{'state':'ARCHIVED'},
                'archive_url':run.get('archive_build_url') or (run.get('external') or {}).get('build_url')}
    _,external_id=target_record(run,target_id)
    root=store.root/'runs'/run['id']
    if root.is_symlink():raise ValueError('DEFINITION_PATH_UNSAFE')
    plan_path=safe_path(root,f'targets/{external_id}/plan.json')
    if not plan_path.is_file():return {'source':{'state':'UNAVAILABLE'},'target':{'state':'UNAVAILABLE'}}
    plan=checked_document(plan_path)
    if plan['plan_id']!=view['plan_id'] or plan['target']['id']!=external_id:raise ValueError('DEFINITION_PLAN_MISMATCH')
    root_rows=[r for r in obj['differences'] if pointer_parts(r['property_path'])[0] in {'exists','presence'}]
    status=presence_status(root_rows)
    return {'source':read_side(root,'source/source-snapshot.json','SOURCE',key,plan,status=='EXTRA'),
            'target':read_side(root,f'observations/{external_id}/target-snapshot.json','TARGET',key,plan,status=='MISSING')}
