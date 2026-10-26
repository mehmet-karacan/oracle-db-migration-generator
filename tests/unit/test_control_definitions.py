import hashlib,json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from oracle_db_migration_generator.control.api import create_app
from test_control_results import completed_run


def local_definition_fixture(tmp_path):
    store,id,target,plan,key=completed_run(tmp_path)
    plan['target']['id']=target;plan['synthetic']=True
    store.update_run(id,external=None,executor='LOCAL',source_commit=plan['source']['commit_sha'],targets=[{'id':target,'plan_id':plan['plan_id'],'status':'COMPLETE'}])
    root=store.root/'runs'/id
    bundle=root/'targets'/target;bundle.mkdir(parents=True);(bundle/'plan.json').write_text(json.dumps(plan),encoding='utf-8')
    payloads={}
    from oracle_db_migration_generator.model.snapshot_io import load_snapshot
    for side,folder in [('source',root/'source'),('target',root/'observations'/target)]:
        document=json.loads(Path(f'examples/{side}-snapshot.example.json').read_bytes())
        document['semantic_digest']=load_snapshot(Path(f'examples/{side}-snapshot.example.json')).semantic_digest
        if side=='target':
            document['target_id']=target;plan['target_snapshot_digest']=document['semantic_digest']
        else:plan['source']['ddl_digest']=document['semantic_digest']
        folder.mkdir(parents=True)
        path=document['objects'][0]['ddl_path'];raw=Path('examples',path).read_bytes();destination=folder/path;destination.parent.mkdir(parents=True);destination.write_bytes(raw)
        (folder/f'{side}-snapshot.json').write_text(json.dumps(document),encoding='utf-8');payloads[side]=raw.decode('utf-8')
    (bundle/'plan.json').write_text(json.dumps(plan),encoding='utf-8')
    return store,id,target,key,payloads


def test_original_definitions_are_exact_no_store_and_project_scoped(tmp_path):
    store,id,target,key,payloads=local_definition_fixture(tmp_path)
    url=f'/api/runs/{id}/results/objects/{key}/definitions?target_id={target}'
    with TestClient(create_app(tmp_path,mode='local',start_workers=False)) as client:
        response=client.get(url)
        assert response.status_code==200 and response.headers['cache-control']=='no-store'
        assert response.json()['source']=={'state':'AVAILABLE','text':payloads['source']}
        assert response.json()['target']=={'state':'AVAILABLE','text':payloads['target']}
        other=store.save_project({'name':'Other','code':'OTHER'},actor='shared')
        assert client.get(url,headers={'x-odmg-project':other['id']}).status_code==404
        assert client.get(url.replace(target,'x'*32)).status_code==404


def test_definitions_verify_blob_hash_and_byte_span(tmp_path):
    store,id,target,key,payloads=local_definition_fixture(tmp_path)
    folder=store.root/'runs'/id/'source';snapshot=folder/'source-snapshot.json';document=json.loads(snapshot.read_bytes())
    obj=document['objects'][0];blob=folder/obj['ddl_path'];original=blob.read_bytes();payload=b'-- header\n'+original+b'-- footer\n';blob.write_bytes(payload)
    for evidence in document['evidence']:
        evidence.update(sha256=hashlib.sha256(payload).hexdigest(),start_byte=10,end_byte=10+len(original))
    snapshot.write_text(json.dumps(document),encoding='utf-8')
    with TestClient(create_app(tmp_path,mode='local',start_workers=False)) as client:
        url=f'/api/runs/{id}/results/objects/{key}/definitions?target_id={target}'
        assert client.get(url).json()['source']['text']==payloads['source']
        blob.write_bytes(payload+b'changed')
        result=client.get(url).json()['source']
        assert result['state']=='INTEGRITY_ERROR' and 'text' not in result


def test_jenkins_definitions_never_read_local_copies(tmp_path):
    store,id,target,key,_=local_definition_fixture(tmp_path)
    store.update_run(id,executor='JENKINS',archive_build_url='https://jenkins.example.test/job/compare/55/')
    with TestClient(create_app(tmp_path,mode='local',start_workers=False)) as client:
        response=client.get(f'/api/runs/{id}/results/objects/{key}/definitions?target_id={target}')
        assert response.json()['source']=={'state':'ARCHIVED'} and response.json()['target']=={'state':'ARCHIVED'}
        assert 'CREATE' not in response.text
@pytest.mark.parametrize('mutation',['escape','identity','missing_blob'])
def test_invalid_or_missing_original_never_becomes_empty_equal_sql(tmp_path,mutation):
    store,id,target,key,_=local_definition_fixture(tmp_path)
    folder=store.root/'runs'/id/'source';snapshot=folder/'source-snapshot.json';doc=json.loads(snapshot.read_bytes());obj=doc['objects'][0]
    if mutation=='escape':obj['ddl_path']='../../outside.sql'
    elif mutation=='identity':obj['identity']['name']='OTHER'
    else:(folder/obj['ddl_path']).unlink()
    snapshot.write_text(json.dumps(doc),encoding='utf-8')
    with TestClient(create_app(tmp_path,mode='local',start_workers=False)) as client:
        result=client.get(f'/api/runs/{id}/results/objects/{key}/definitions?target_id={target}').json()['source']
        assert result['state'] in {'INTEGRITY_ERROR','UNAVAILABLE'} and 'text' not in result
