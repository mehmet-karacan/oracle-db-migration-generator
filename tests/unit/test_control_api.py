import time

from fastapi.testclient import TestClient

from test_control_store import connection


def client(tmp_path,**kwargs):
    from oracle_db_migration_generator.control.api import create_app
    return TestClient(create_app(tmp_path,start_workers=False,**kwargs))


def test_anonymous_and_forged_proxy_headers_are_rejected(tmp_path):
    with client(tmp_path) as c:
        assert c.get('/api/session').status_code==401
        assert c.get('/api/connections',headers={'x-odmg-user':'admin','x-odmg-role':'admin'}).status_code==401


def test_api_crud_validates_and_does_not_echo_secrets(tmp_path):
    with client(tmp_path,mode='local') as c:
        bad=c.post('/api/connections',json=connection(host='bad/host'))
        assert bad.status_code==422 and 'synthetic-only-secret' not in bad.text
        saved=c.post('/api/connections',json=connection()).json()
        assert 'synthetic-only-secret' not in c.get('/api/connections').text
        profile=c.post('/api/profiles',json={'name':'Comparison','source':{'kind':'ORACLE','connection_id':saved['id'],'schemas':['APP']},'target_ids':[saved['id']],
            'target_mappings':{saved['id']:[{'source_schema':'APP','target_schema':'APP'}]}}).json()
        run=c.post('/api/runs',json={'profile_id':profile['id']})
        assert run.status_code==202 and run.json()['status']=='QUEUED'
        assert c.get('/api/runs/'+run.json()['id']).json()['spec']['profile']['source']['kind']=='ORACLE'
        assert c.get('/api/runs/'+run.json()['id']+'/artifacts/../../vault.key').status_code in {404,400}


def test_edit_access_info_returns_only_username_and_preserves_secret(tmp_path):
    with client(tmp_path,mode='local') as c:
        saved=c.post('/api/connections',json=connection()).json()
        before=c.app.state.store.connection(saved['id'])
        url=f"/api/connections/{saved['id']}/access-info?revision={saved['revision']}"
        response=c.get(url)
        assert response.status_code==200
        assert response.headers['cache-control']=='no-store'
        assert response.json()=={'username':'APP','credential_configured':True}
        assert 'synthetic-only-secret' not in response.text
        assert c.app.state.store.connection(saved['id'])==before
        updated=c.post('/api/connections',json={**saved,'username':'APP','password':None}).json()
        assert c.app.state.store.credentials(saved['id']).password=='synthetic-only-secret'
        assert c.get(url).status_code==409
        empty=c.post('/api/connections',json={'kind':'GIT','name':'Public','repository':'https://example.test/public.git'}).json()
        assert c.get(f"/api/connections/{empty['id']}/access-info?revision=1").json()=={'username':None,'credential_configured':False}
        assert updated['revision']==saved['revision']+1
    with client(tmp_path) as c:
        assert c.get(url).status_code==401


def test_operator_cannot_edit_settings_or_use_an_unassigned_connection(tmp_path):
    from oracle_db_migration_generator.control.auth import signature
    from oracle_db_migration_generator.control.store import ControlStore
    store=ControlStore(tmp_path);con=store.save_connection(connection(allowed_users=['someone']),actor='admin')
    p=store.save_profile({'name':'Restricted','source':{'kind':'ORACLE','connection_id':con['id'],'schemas':['APP']},'target_ids':[con['id']]},actor='admin')
    key='synthetic-signing-key-more-than-32-characters';stamp=str(int(time.time()))
    h={'x-odmg-user':'operator','x-odmg-role':'operator','x-odmg-timestamp':stamp,
       'x-odmg-signature':signature(key,'operator','operator',stamp)}
    with client(tmp_path,proxy_key=key,shared_workspace=False) as c:
        assert c.get('/api/connections',headers=h).json()==[]
        assert c.put('/api/settings',json=store.settings(),headers=h).status_code==403
        assert c.get(f"/api/connections/{con['id']}/access-info?revision=1",headers=h).status_code==403
        assert c.post('/api/runs',json={'profile_id':p['id']},headers=h).status_code==403


def test_source_capture_failure_is_not_zero_differences(tmp_path):
    from oracle_db_migration_generator.control.store import ControlStore
    from oracle_db_migration_generator.control.runner import execute_run
    from oracle_db_migration_generator.oracle.collector import TargetObservation
    store=ControlStore(tmp_path);con=store.save_connection(connection(),actor='admin')
    p=store.save_profile({'name':'Capture fail','source':{'kind':'ORACLE','connection_id':con['id'],'schemas':['APP']},'target_ids':[con['id']]},actor='admin')
    run=store.create_run(p['id'],actor='admin',role='admin')
    execute_run(store,run['id'],source_collector=lambda *a,**kw:TargetObservation(None,{'status':'INCONSISTENT'}))
    result=store.run(run['id'])
    assert result['status']=='FAILED' and result['error_code']=='SOURCE_CAPTURE_INCONSISTENT'
    assert result['targets']==[] and result['finished_at'] is not None


def test_changed_parser_budget_changes_prepared_cache_identity(tmp_path):
    from oracle_db_migration_generator.control.runtime import runtime_settings
    from oracle_db_migration_generator.parsing.budgets import parser_timeout
    assert parser_timeout(1,'TABLE')==30
    with runtime_settings({'parser_regular_seconds':40}):
        assert parser_timeout(1,'TABLE')==40
    assert parser_timeout(1,'TABLE')==30


def test_duplicate_worker_cannot_replace_a_finished_result(tmp_path):
    from oracle_db_migration_generator.control.store import ControlStore
    from oracle_db_migration_generator.control.runner import execute_run
    store=ControlStore(tmp_path);con=store.save_connection(connection(),actor='admin')
    p=store.save_profile({'name':'Once','source':{'kind':'ORACLE','connection_id':con['id'],'schemas':['APP']},'target_ids':[con['id']]},actor='admin')
    run=store.create_run(p['id'],actor='admin',role='admin')
    store.update_run(run['id'],status='COMPLETE',stage='FINISHED',finished_at='2026-10-24T00:00:00+00:00')
    def forbidden(*args,**kwargs):raise AssertionError('FINISHED_JOB_REEXECUTED')
    execute_run(store,run['id'],source_collector=forbidden)
    assert store.run(run['id'])['status']=='COMPLETE'


def test_abandoned_queue_claim_is_reported_as_interrupted(tmp_path):
    from oracle_db_migration_generator.control.store import ControlStore
    from oracle_db_migration_generator.control.queue import LocalQueue,process_alive
    import os
    assert process_alive(os.getpid())
    store=ControlStore(tmp_path);con=store.save_connection(connection(),actor='admin')
    p=store.save_profile({'name':'Queue','source':{'kind':'ORACLE','connection_id':con['id'],'schemas':['APP']},'target_ids':[con['id']]},actor='admin')
    run=store.create_run(p['id'],actor='admin',role='admin')
    store.update_run(run['id'],claimed=True,claimed_at='2000-01-01T00:00:00+00:00')
    LocalQueue(store).tick()
    assert store.run(run['id'])['error_code']=='WORKER_INTERRUPTED'
