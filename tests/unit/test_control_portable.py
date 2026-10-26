from unittest.mock import patch
import io
import zipfile

from fastapi.testclient import TestClient
import pytest

from oracle_db_migration_generator.control.api import create_app
from oracle_db_migration_generator.control.runner import execute_run
from test_portable_stream import packet,records


def test_project_bound_import_export_and_snapshot_comparison_are_offline(tmp_path):
    app=create_app(tmp_path,mode='local',start_workers=False);store=app.state.store
    with TestClient(app) as client:
        sky=store.list_records('project')[0]
        other=store.save_project({'name':'Other','code':'OTHER'},actor='shared')
        def upload(values,name):
            response=client.post('/api/captures/import?name='+name,content=packet(values),headers={'content-type':'application/octet-stream','x-odmg-project':sky['id']})
            assert response.status_code==201,response.text
            return response.json()
        source=upload(records(),'Desired');target=upload(records(inventory=[]),'Actual')
        assert source['kind']=='SNAPSHOT' and source['capture_schemas']==['APP'] and not source['credential_configured']
        assert not (store.root/'captures'/source['capture_id']/'capture.odmg.jsonl').is_symlink()
        assert client.get('/api/connections',headers={'x-odmg-project':other['id']}).json()==[]
        wrong={**source,'project_id':other['id']}
        assert client.post('/api/connections',json=wrong,headers={'x-odmg-project':other['id']}).status_code==422
        request={'name':'Imported comparison','project_id':sky['id'],'source':{'kind':'SNAPSHOT','connection_id':source['id'],'schemas':['APP']},'target_ids':[target['id']],
                 'target_mappings':{target['id']:[{'source_schema':'APP','target_schema':'APP'}]},
                 'capture_filter':{'object_types':['TABLE'],'object_names':['DEMO']}}
        profile=client.post('/api/profiles',json=request)
        assert profile.status_code==200,profile.text
        assert client.post('/api/runs',json={'profile_id':profile.json()['id'],'executor':'JENKINS'}).status_code==422
        response=client.post('/api/runs',json={'profile_id':profile.json()['id'],'executor':'LOCAL'})
        assert response.status_code==202,response.text
        id=response.json()['id']
        with patch('oracle_db_migration_generator.control.runner.initialize_driver',side_effect=AssertionError('NO_ORACLE_CLIENT')):
            execute_run(store,id)
        run=store.run(id)
        assert run['report_available'] and run['source_performance']['source_kind']=='SNAPSHOT',run
        assert any(p for p in (store.root/'runs'/id/'targets'/target['id']/'objects').rglob('*.sql'))
        response=client.post('/api/captures/package',json={'schemas':['APP'],'table_names':['DEMO']})
        assert response.status_code==200,response.text
        with zipfile.ZipFile(io.BytesIO(response.content)) as package:
            assert {'README.md','collect.sql','run_export.sql','New-Capture.ps1','selection.json'}==set(package.namelist())
            assert b':p_schemas' in package.read('run_export.sql')


def test_bad_import_does_not_create_a_connection(tmp_path):
    app=create_app(tmp_path,mode='local',start_workers=False)
    with TestClient(app) as client:
        response=client.post('/api/captures/import?name=Broken',content=packet(records())[:-30],headers={'content-type':'application/octet-stream'})
        assert response.status_code==422
        assert app.state.store.list_records('connection')==[]


def test_snapshot_integrity_and_credentials_are_enforced(tmp_path):
    app=create_app(tmp_path,mode='local',start_workers=False);store=app.state.store
    with TestClient(app) as client:
        saved=client.post('/api/captures/import?name=Imported',content=packet(records()),headers={'content-type':'application/octet-stream'}).json()
        assert client.post('/api/connections',json={**saved,'username':'APP','password':'secret'}).status_code==422
        file=store.root/'captures'/saved['capture_id']/'capture.odmg.jsonl'
        file.write_bytes(packet(records('CREATE TABLE APP.DEMO (ID DATE);')))
        with pytest.raises(ValueError,match='CAPTURE_INTEGRITY'):store.load_capture(saved)


def test_imported_comparison_runs_in_the_real_worker_process(tmp_path):
    import subprocess,sys
    from oracle_db_migration_generator.control.store import ControlStore,DEFAULT_PROJECT_ID
    store=ControlStore(tmp_path)
    source=store.import_capture(packet(records()),name='Source',project_id=DEFAULT_PROJECT_ID,actor='shared')
    target=store.import_capture(packet(records(inventory=[])),name='Target',project_id=DEFAULT_PROJECT_ID,actor='shared')
    profile=store.save_profile({'name':'Worker','source':{'kind':'SNAPSHOT','connection_id':source['id'],'schemas':['APP']},
        'target_ids':[target['id']],'capture_filter':{'object_types':['TABLE'],'object_names':['DEMO'],'data_types':['NUMBER']}},actor='shared')
    run=store.create_run(profile['id'],actor='shared',role='shared')
    result=subprocess.run([sys.executable,'-m','oracle_db_migration_generator.control.worker','--root',str(tmp_path),'--run',run['id']],capture_output=True,timeout=60)
    stored=store.run(run['id'])
    assert result.returncode==0 and stored['status']=='COMPLETE',{'status':stored['status'],'error':stored.get('error_code'),'stderr':result.stderr[-1000:]}
