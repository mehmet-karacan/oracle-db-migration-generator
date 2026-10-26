import copy
import json
from datetime import datetime,timedelta,timezone

import pytest
from fastapi.testclient import TestClient

from oracle_db_migration_generator.control.api import create_app
from test_control_store import connection


def setup_binding(tmp_path):
    from oracle_db_migration_generator.control.jenkins_browser import spec_fingerprint
    app=create_app(tmp_path/'state',mode='local',start_workers=False)
    s=app.state.store
    c=s.save_connection(connection(),actor='shared')
    g=s.save_connection({'kind':'GIT','name':'Source','repository':'https://example.test/source.git'},actor='shared')
    p=s.save_profile({'name':'Live','source':{'kind':'GIT','connection_id':g['id'],'schemas':['APP']},'target_ids':[c['id']]},actor='shared')
    spec=s.run_spec(p['id'],actor='shared',role='shared')
    binding={'project_id':p['project_id'],'profile_id':p['id'],'fingerprint':spec_fingerprint(spec),
             'job_url':'https://jenkins.example.test/job/compare/','schema_scope':'APP','target_map':{c['id']:'LIVE-APP'}}
    path=tmp_path/'bindings.json';path.write_text(json.dumps([binding]))
    return app,s,p,binding,path


def test_handoff_never_queues_local_worker_and_rejects_changed_scope(tmp_path,monkeypatch):
    app,s,p,b,path=setup_binding(tmp_path)
    monkeypatch.setenv('ODMG_UI_JENKINS_BINDINGS',str(path))
    with TestClient(app,client=('127.0.0.1',1234)) as client:
        response=client.post('/api/runs',json={'profile_id':p['id']})
        assert response.status_code==202
        run=response.json()
        assert run['status']=='AWAITING_JENKINS'
        assert s.scheduler_runs()==[] and s.reserve_next_run(1) is None
        assert run['external']['launch_url']==b['job_url']+'build?delay=0sec'
        s.save_profile({**p,'compare_physical_storage':True},actor='shared')
        assert client.post('/api/runs',json={'profile_id':p['id']}).status_code==409
        assert len(s.runs())==1


def document(run,binding):
    start=datetime.fromisoformat(run['created_at'])+timedelta(seconds=1)
    return {'schema_version':'run/1.0','run_id':'build-55','synthetic':False,
        'started_at':start.isoformat(),'finished_at':(start+timedelta(seconds=70)).isoformat(),
        'source_commit':'a'*40,'status':'PARTIAL','exit_code':10,'build_url':binding['job_url']+'55/',
        'build_number':55,'artifact_git_sha':None,'targets':[{'id':'LIVE-APP','status':'REVIEW_REQUIRED',
        'difference_count':None,'plan_id':'b'*64,'plan_path':'targets/LIVE-APP/plan.json',
        'captured_at':(start+timedelta(seconds=5)).isoformat(),'error_code':None,'publication':'NOT_REQUESTED'}]}


def test_link_requires_fresh_matching_real_result_and_keeps_unknown(tmp_path,monkeypatch):
    from oracle_db_migration_generator.control.jenkins_browser import link_completed_run
    app,s,p,b,path=setup_binding(tmp_path);monkeypatch.setenv('ODMG_UI_JENKINS_BINDINGS',str(path))
    with TestClient(app,client=('127.0.0.1',1234)) as client:
        run=client.post('/api/runs',json={'profile_id':p['id']}).json()
    run=s.update_run(run['id'],created_at=(datetime.now(timezone.utc)-timedelta(seconds=120)).isoformat())
    d=document(run,b)
    for change in [{'synthetic':True},{'source_commit':None},{'started_at':'2020-01-01T00:00:00+00:00'},
                   {'build_url':'https://elsewhere.test/55/'},{'run_id':'build-54'},
                   {'finished_at':'2020-01-01T00:00:00+00:00'}]:
        with pytest.raises(ValueError):link_completed_run(s,run['id'],{**d,**change})
    wrong=copy.deepcopy(d);wrong['targets'][0]['id']='WRONG'
    with pytest.raises(ValueError):link_completed_run(s,run['id'],wrong)
    linked=link_completed_run(s,run['id'],d)
    assert linked['targets'][0]['difference_count'] is None
    assert linked['started_at']==d['started_at'] and linked['status']=='PARTIAL'
    assert linked['external']['verification']=='BROWSER_OBSERVED'
    assert linked['external']['report_url']==b['job_url']+'55/artifact/output/runs/build-55/index.html'
    assert not (s.root/'runs').exists()  # No SQL or bundle copied locally.
    assert link_completed_run(s,run['id'],d)['id']==run['id']
    with pytest.raises(ValueError):link_completed_run(s,run['id'],{**d,'source_commit':'c'*40})


def test_source_timing_must_match_observed_run_and_fit_elapsed_time(tmp_path,monkeypatch):
    from oracle_db_migration_generator.control.jenkins_browser import link_completed_run
    app,s,p,b,path=setup_binding(tmp_path);monkeypatch.setenv('ODMG_UI_JENKINS_BINDINGS',str(path))
    with TestClient(app,client=('127.0.0.1',1234)) as client:
        run=client.post('/api/runs',json={'profile_id':p['id']}).json()
    run=s.update_run(run['id'],created_at=(datetime.now(timezone.utc)-timedelta(seconds=120)).isoformat())
    d=document(run,b)
    timing={'schema_version':'source-preparation-performance/1.0','source_commit':'a'*40,'total_seconds':22.8,'cache_status':'HIT_VERIFIED'}
    for bad in [{'source_commit':'c'*40},{'total_seconds':-1},{'total_seconds':float('nan')},{'total_seconds':10000}]:
        with pytest.raises(ValueError):link_completed_run(s,run['id'],d,performance={**timing,**bad})
    linked=link_completed_run(s,run['id'],d,performance=timing)
    assert linked['source_performance']=={'seconds':22.8,'source_kind':'GIT','cache_status':'HIT_VERIFIED'}


def test_one_observed_build_cannot_complete_two_ui_requests(tmp_path,monkeypatch):
    from oracle_db_migration_generator.control.jenkins_browser import link_completed_run
    app,s,p,b,path=setup_binding(tmp_path);monkeypatch.setenv('ODMG_UI_JENKINS_BINDINGS',str(path))
    with TestClient(app,client=('127.0.0.1',1234)) as client:
        runs=[client.post('/api/runs',json={'profile_id':p['id']}).json() for _ in range(2)]
    runs=[s.update_run(r['id'],created_at=(datetime.now(timezone.utc)-timedelta(seconds=120)).isoformat()) for r in runs]
    d=document(runs[1],b)
    link_completed_run(s,runs[0]['id'],d)
    with pytest.raises(ValueError,match='JENKINS_BUILD_ALREADY_LINKED'):link_completed_run(s,runs[1]['id'],d)
    assert s.run(runs[1]['id'])['status']=='AWAITING_JENKINS'


def test_linking_different_results_concurrently_has_only_one_winner(tmp_path,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from oracle_db_migration_generator.control.jenkins_browser import link_completed_run
    app,s,p,b,path=setup_binding(tmp_path);monkeypatch.setenv('ODMG_UI_JENKINS_BINDINGS',str(path))
    with TestClient(app,client=('127.0.0.1',1234)) as client:
        run=client.post('/api/runs',json={'profile_id':p['id']}).json()
    run=s.update_run(run['id'],created_at=(datetime.now(timezone.utc)-timedelta(seconds=120)).isoformat())
    gate=Barrier(2);original=s.run
    def read(id):
        value=original(id);gate.wait(timeout=5);return value
    monkeypatch.setattr(s,'run',read)
    def link(commit):
        try:return link_completed_run(s,run['id'],{**document(run,b),'source_commit':commit})['source_commit']
        except ValueError:return 'REJECTED'
    with ThreadPoolExecutor(2) as pool:results=list(pool.map(link,['a'*40,'c'*40]))
    assert results.count('REJECTED')==1


def test_persisted_jenkins_mode_cannot_fall_back_to_local_for_another_project(tmp_path):
    app,s,p,b,path=setup_binding(tmp_path)
    (s.root/'jenkins-bindings.json').write_text(path.read_text())
    other=s.save_project({'name':'Another','code':'ANOTHER'},actor='shared')
    c=s.save_connection(connection(project_id=other['id']),actor='shared')
    profile=s.save_profile({'project_id':other['id'],'name':'Other run','source':{'kind':'ORACLE','connection_id':c['id'],'schemas':['APP']},'target_ids':[c['id']]},actor='shared')
    with TestClient(app,client=('127.0.0.1',1234)) as client:
        assert client.post('/api/runs',json={'profile_id':p['id']}).json()['status']=='AWAITING_JENKINS'
        assert client.post('/api/runs',json={'profile_id':profile['id'],'project_id':other['id']}).status_code==409
    assert s.scheduler_runs()==[]


def test_normal_aggregate_uuid_is_linked_to_its_build_artifact_path(tmp_path,monkeypatch):
    from oracle_db_migration_generator.control.jenkins_browser import link_completed_run
    app,s,p,b,path=setup_binding(tmp_path);monkeypatch.setenv('ODMG_UI_JENKINS_BINDINGS',str(path))
    with TestClient(app,client=('127.0.0.1',1234)) as client:
        run=client.post('/api/runs',json={'profile_id':p['id']}).json()
    run=s.update_run(run['id'],created_at=(datetime.now(timezone.utc)-timedelta(seconds=120)).isoformat())
    d={**document(run,b),'run_id':'86c108c6-992f-4139-8ad0-47aad1aac20e'}
    linked=link_completed_run(s,run['id'],d)
    assert linked['external']['report_url'].endswith('/55/artifact/output/runs/build-55/index.html')
    assert linked['external']['canonical_run_id']==d['run_id']
