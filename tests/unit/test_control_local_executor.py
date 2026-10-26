from fastapi.testclient import TestClient
from unittest.mock import patch
from oracle_db_migration_generator.control.api import create_app
from test_control_store import connection


def test_explicit_local_execution_bypasses_jenkins_binding_and_keeps_sql_private(tmp_path):
    app=create_app(tmp_path,mode='local',start_workers=False);store=app.state.store
    c=store.save_connection(connection(),actor='shared')
    p=store.save_profile({'name':'Local','source':{'kind':'ORACLE','connection_id':c['id'],'schemas':['APP']},'target_ids':[c['id']]},actor='shared')
    with TestClient(app) as client,patch('oracle_db_migration_generator.control.jenkins_browser.approved_handoff',side_effect=AssertionError('LOCAL_MUST_NOT_DISPATCH_JENKINS')):
        r=client.post('/api/runs',json={'profile_id':p['id'],'executor':'LOCAL'})
        assert r.status_code==202
        run=store.run(r.json()['id'])
        assert run['executor']=='LOCAL' and run['artifact_mode']=='LOCAL_PRIVATE' and 'external' not in run
        folder=store.root/'runs'/run['id']/'targets'/c['id'];folder.mkdir(parents=True)
        sql=b'CREATE TABLE "APP"."DEMO" (\n    "TITLE" VARCHAR2(80)\n);\n'
        (folder/'demo.sql').write_bytes(sql)
        response=client.get(f"/api/runs/{run['id']}/artifacts/targets/{c['id']}/demo.sql")
        assert response.content==sql and response.headers['cache-control']=='no-store'
        other=store.save_project({'name':'Other','code':'OTHER'},actor='shared')
        assert client.get(f"/api/runs/{run['id']}/artifacts/targets/{c['id']}/demo.sql",headers={'x-odmg-project':other['id']}).status_code==404

def test_local_scheduler_never_claims_jenkins_runs(tmp_path):
    app=create_app(tmp_path,mode='local',start_workers=False);store=app.state.store
    c=store.save_connection(connection(),actor='shared')
    p=store.save_profile({'name':'Mixed','source':{'kind':'ORACLE','connection_id':c['id'],'schemas':['APP']},'target_ids':[c['id']]},actor='shared')
    remote=store.create_run(p['id'],actor='shared',role='shared',executor='JENKINS')
    local=store.create_run(p['id'],actor='shared',role='shared',executor='LOCAL')
    assert [r['id'] for r in store.scheduler_runs()]==[local['id']]
    assert store.reserve_next_run(4)['id']==local['id']
    assert store.reserve_next_run(4) is None
    assert not store.run(remote['id']).get('claimed')


def test_explicit_jenkins_does_not_fall_back_to_local(tmp_path,monkeypatch):
    for key in ('ODMG_UI_JENKINS_JOB_URL','ODMG_UI_JENKINS_USER','ODMG_UI_JENKINS_TOKEN'):monkeypatch.delenv(key,raising=False)
    app=create_app(tmp_path,mode='local',start_workers=False);store=app.state.store
    c=store.save_connection(connection(),actor='shared')
    p=store.save_profile({'name':'Remote','source':{'kind':'ORACLE','connection_id':c['id'],'schemas':['APP']},'target_ids':[c['id']]},actor='shared')
    with TestClient(app) as client,patch('oracle_db_migration_generator.control.jenkins_browser.approved_handoff',return_value=None):
        response=client.post('/api/runs',json={'profile_id':p['id'],'executor':'JENKINS'})
        assert response.status_code==503 and response.json()['detail']=='JENKINS_EXECUTOR_NOT_CONFIGURED'
        assert store.runs()==[]

def test_proxy_runtime_rejects_local_execution(tmp_path):
    import time
    from oracle_db_migration_generator.control.auth import signature
    key='synthetic-signing-key-more-than-32-characters'
    app=create_app(tmp_path,mode='proxy',proxy_key=key,start_workers=False);store=app.state.store
    c=store.save_connection(connection(),actor='shared')
    p=store.save_profile({'name':'Proxy','source':{'kind':'ORACLE','connection_id':c['id'],'schemas':['APP']},'target_ids':[c['id']]},actor='shared')
    stamp=str(int(time.time()));headers={'x-odmg-user':'shared','x-odmg-role':'admin','x-odmg-timestamp':stamp,'x-odmg-signature':signature(key,'shared','admin',stamp)}
    with TestClient(app,headers=headers) as client:
        assert client.get('/api/session').json()['local_execution_available'] is False
        response=client.post('/api/runs',json={'profile_id':p['id'],'executor':'LOCAL'})
        assert response.status_code==403 and response.json()['detail']=='LOCAL_EXECUTOR_UNAVAILABLE'
        assert store.runs()==[]

def test_jenkins_sql_links_only_resolve_to_its_verified_archive(tmp_path):
    from oracle_db_migration_generator.control.results import _sql_url
    app=create_app(tmp_path,mode='local',start_workers=False);store=app.state.store
    c=store.save_connection(connection(),actor='shared')
    p=store.save_profile({'name':'Remote','source':{'kind':'ORACLE','connection_id':c['id'],'schemas':['APP']},'target_ids':[c['id']]},actor='shared')
    run=store.create_run(p['id'],actor='shared',role='shared',executor='JENKINS')
    assert _sql_url(run,c['id'],'objects/demo.sql') is None
    url='https://jenkins.example.test/job/compare/55/'
    run=store.update_run(run['id'],archive_build_url=url)
    assert _sql_url(run,c['id'],'objects/demo.sql')==url+f"artifact/output/runs/build-55/targets/{c['id']}/objects/demo.sql/*view*/"
    folder=store.root/'runs'/run['id']/'targets'/c['id'];folder.mkdir(parents=True)
    (folder/'demo.sql').write_text('SELECT 1 FROM DUAL;',encoding='utf-8')
    with TestClient(app) as client:
        assert client.get(f"/api/runs/{run['id']}/artifacts/targets/{c['id']}/demo.sql").status_code==404
