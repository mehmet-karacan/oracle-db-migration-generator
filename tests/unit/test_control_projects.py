import time
import pytest
from fastapi.testclient import TestClient

from oracle_db_migration_generator.control.store import ControlStore
from test_control_store import connection


def test_project_scope_is_persisted_and_cross_project_profile_is_rejected(tmp_path):
    store=ControlStore(tmp_path)
    sky=store.list_records('project')[0]
    other=store.save_project({'name':'Other project','code':'OTHER'},actor='shared')
    a=store.save_connection(connection(project_id=sky['id']),actor='shared')
    b=store.save_connection(connection(name='Other Oracle',project_id=other['id']),actor='shared')
    assert [c['id'] for c in store.list_records('connection',project_id=other['id'])]==[b['id']]
    with pytest.raises(ValueError,match='PROJECT_SCOPE_MISMATCH'):
        store.save_profile({'name':'Wrong','project_id':sky['id'],'source':{'kind':'ORACLE','connection_id':a['id'],'schemas':['APP']},'target_ids':[b['id']]},actor='shared')
    with pytest.raises(ValueError,match='PROJECT_MEMBERSHIP_IMMUTABLE'):
        store.save_connection({**a,'project_id':other['id']},actor='shared')


def test_legacy_records_default_to_sky_and_runs_keep_their_project(tmp_path):
    store=ControlStore(tmp_path);sky=store.list_records('project')[0]
    c=store.save_connection(connection(),actor='admin')
    p=store.save_profile({'name':'Legacy','source':{'kind':'ORACLE','connection_id':c['id'],'schemas':['APP']},'target_ids':[c['id']]},actor='admin')
    run=store.create_run(p['id'],actor='shared',role='shared')
    assert c['project_id']==p['project_id']==run['project_id']==sky['id']
    assert store.runs(project_id=sky['id'])[0]['id']==run['id']
    assert store.runs(project_id='0'*32)==[]


def test_shared_workspace_has_one_capability_set_but_requires_valid_identity(tmp_path,monkeypatch):
    from oracle_db_migration_generator.control.api import create_app
    from oracle_db_migration_generator.control.auth import signature
    key='synthetic-only-signing-key-long-enough';stamp=str(int(time.time()))
    app=create_app(tmp_path,proxy_key=key,start_workers=False)
    h=lambda user:{'x-odmg-user':user,'x-odmg-role':'viewer','x-odmg-timestamp':stamp,'x-odmg-signature':signature(key,user,'viewer',stamp)}
    with TestClient(app) as client:
        assert client.get('/api/session').status_code==401
        assert client.get('/api/session',headers=h('one')).json()['role']=='shared'
        sky=client.get('/api/projects',headers=h('one')).json()[0]
        saved=client.post('/api/connections',headers=h('one'),json=connection(project_id=sky['id'])).json()
        assert client.get('/api/connections',headers=h('two')).json()[0]['id']==saved['id']
        assert client.get('/api/settings',headers=h('two')).status_code==200
        p=client.post('/api/profiles',headers=h('one'),json={'name':'Shared','project_id':sky['id'],'source':{'kind':'ORACLE','connection_id':saved['id'],'schemas':['APP']},'target_ids':[saved['id']],
            'target_mappings':{saved['id']:[{'source_schema':'APP','target_schema':'APP'}]}}).json()
        # Unconfigured Jenkins is explicit; the shared caller was authorized first.
        assert client.post('/api/runs',headers=h('two'),json={'profile_id':p['id'],'project_id':sky['id']}).status_code==503
        r=app.state.store.create_run(p['id'],actor='one',role='shared')
        assert client.get('/api/runs/'+r['id'],headers=h('two')).status_code==200
        assert client.get('/api/connections?project_id='+'0'*32,headers=h('two')).json()==[]
