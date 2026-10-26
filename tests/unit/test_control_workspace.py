from fastapi.testclient import TestClient
import pytest
from oracle_db_migration_generator.control.api import create_app
from test_control_store import connection


def test_settings_and_run_snapshot_are_project_scoped(tmp_path):
    app=create_app(tmp_path,mode='local',start_workers=False)
    store=app.state.store
    sky=store.list_records('project')[0]['id']
    other=store.save_project({'name':'Other','code':'OTHER'},actor='shared')['id']
    with TestClient(app) as client:
        initial=client.get('/api/settings',headers={'x-odmg-project':sky}).json()
        saved=client.put('/api/settings',headers={'x-odmg-project':sky},json={**initial,'git_attempts':5}).json()
        different=client.get('/api/settings',headers={'x-odmg-project':other}).json()
        assert saved['project_id']==sky
        assert different['project_id']==other and different['git_attempts']==3
        c=store.save_connection(connection(project_id=other),actor='shared')
        p=store.save_profile({'name':'Other','project_id':other,'source':{'kind':'ORACLE','connection_id':c['id'],'schemas':['APP']},'target_ids':[c['id']]},actor='shared')
        assert store.run_spec(p['id'],actor='shared',role='shared')['settings']['project_id']==other
        assert client.put('/api/settings',headers={'x-odmg-project':other},json=saved).status_code==422


def test_all_record_routes_reject_other_project_ids_before_work(tmp_path,monkeypatch):
    app=create_app(tmp_path,mode='local',start_workers=False);store=app.state.store
    sky=store.list_records('project')[0]['id']
    other=store.save_project({'name':'Other','code':'OTHER'},actor='shared')['id']
    c=store.save_connection(connection(project_id=sky),actor='shared')
    p=store.save_profile({'name':'Sky','source':{'kind':'ORACLE','connection_id':c['id'],'schemas':['APP']},'target_ids':[c['id']]},actor='shared')
    r=store.create_run(p['id'],actor='shared',role='shared')
    monkeypatch.setattr('oracle_db_migration_generator.control.api.isolated_connection_test',lambda *a,**k:(_ for _ in ()).throw(AssertionError('probe must not run')))
    with TestClient(app,headers={'x-odmg-project':other}) as client:
        assert client.get('/api/connections').json()==[]
        assert client.get('/api/profiles').json()==[]
        assert client.get('/api/runs').json()==[]
        for path in [f"/connections/{c['id']}/access-info?revision=1",f"/runs/{r['id']}",f"/runs/{r['id']}/artifacts/index.html",f"/runs/{r['id']}/operations?target_id={c['id']}",f"/runs/{r['id']}/results/objects?target_id={c['id']}"]:
            assert client.get('/api'+path).status_code==404,path
        assert client.post(f"/api/connections/{c['id']}/test",json={}).status_code==404
        assert client.post('/api/connections',json={**c,'username':'APP','password':None}).status_code==422
        assert client.post('/api/runs',json={'profile_id':p['id']}).status_code==404
        assert client.get('/api/runs?project_id='+sky).status_code==422
    # Artifact URLs carry the project even when opened without a fetch header.
    with TestClient(app) as client:
        assert client.get(f"/api/runs/{r['id']}?project_id={other}").status_code==404


def test_project_parallel_limit_does_not_block_another_project(tmp_path):
    app=create_app(tmp_path,mode='local',start_workers=False);store=app.state.store
    other=store.save_project({'name':'Other','code':'OTHER'},actor='shared')['id']
    runs=[]
    from oracle_db_migration_generator.control.store import DEFAULT_PROJECT_ID
    for project in [DEFAULT_PROJECT_ID,other]:
        c=store.save_connection(connection(project_id=project),actor='shared')
        p=store.save_profile({'name':'Compare','project_id':project,'source':{'kind':'ORACLE','connection_id':c['id'],'schemas':['APP']},'target_ids':[c['id']]},actor='shared')
        runs.append(store.create_run(p['id'],actor='shared',role='shared'))
    assert store.begin_run(runs[0]['id'])
    assert store.begin_run(runs[1]['id'])


@pytest.mark.parametrize('status',['COMPLETE','FAILED'])
def test_terminal_claim_does_not_consume_project_capacity(tmp_path,status):
    app=create_app(tmp_path,mode='local',start_workers=False);store=app.state.store
    c=store.save_connection(connection(),actor='shared')
    p=store.save_profile({'name':'Compare','source':{'kind':'ORACLE','connection_id':c['id'],'schemas':['APP']},'target_ids':[c['id']]},actor='shared')
    first=store.create_run(p['id'],actor='shared',role='shared')
    assert store.reserve_next_run(4)['id']==first['id']
    assert store.begin_run(first['id'])
    store.update_run(first['id'],status=status)
    second=store.create_run(p['id'],actor='shared',role='shared')
    assert store.reserve_next_run(4)['id']==second['id']
    assert store.begin_run(second['id'])
