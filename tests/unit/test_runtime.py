import json
from pathlib import Path

from oracle_db_migration_generator.cli import main
from oracle_db_migration_generator.model.serialization import canonical_bytes
from tests.factories import source,actual,ROOT


def save_snapshot(snapshot,root,name):
    root.mkdir()
    for obj in snapshot.objects:
        if obj.ddl_path and obj.raw_ddl:
            path=root/obj.ddl_path;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(obj.raw_ddl)
    # The simple one-object fixture uses its full original source span.
    path=root/name;path.write_bytes(canonical_bytes(snapshot.to_dict()))
    return path


def test_offline_cli_produces_reviewable_plan_without_network(tmp_path,capsys,monkeypatch):
    def no_network(*args,**kwargs): raise AssertionError('Unexpected network')
    monkeypatch.setattr('socket.create_connection',no_network)
    desired=save_snapshot(source('CREATE TABLE APP.T(ID NUMBER);'),tmp_path/'source','source-snapshot.json')
    observed=save_snapshot(actual(),tmp_path/'target','target-snapshot.json')
    code=main(['plan-offline','--source-snapshot',str(desired),'--target-snapshot',str(observed),
               '--source-profile',str(ROOT/'examples/source-profile.example.json'),'--output',str(tmp_path/'bundle')])
    assert code==0
    assert json.loads(capsys.readouterr().out.splitlines()[-1])['decision']=='READY'
    assert main(['verify-bundle','--bundle',str(tmp_path/'bundle')])==0


def test_read_only_live_failure_becomes_error_receipt_not_zero_plan(tmp_path):
    from oracle_db_migration_generator.runtime.worker import run_target
    from oracle_db_migration_generator.oracle.collector import TargetObservation
    from oracle_db_migration_generator.config.loader import load_targets
    from tests.factories import profile
    selected=profile();target=load_targets(ROOT/'examples/targets.example.json',('DEMO-TEST',))[0]
    result=run_target(source('CREATE TABLE APP.T(ID NUMBER);'),target,selected,None,tmp_path/'run',
                      collect=lambda *a,**k: TargetObservation(None,{'status':'ERROR','target_id':target.id,'difference_count':None,
                          'finished_at':'2026-10-19T00:00:00Z','schemas':[{'error_code':'ORA-01031'}]}))
    assert result['difference_count'] is None and result['plan_id'] is None
    assert not (tmp_path/'run'/'targets'/target.id/'plan.json').exists()
    assert (tmp_path/'run'/'targets'/target.id/'target-error.json').exists()


def test_aggregate_rejects_result_status_that_disagrees_with_plan(tmp_path):
    import pytest
    from oracle_db_migration_generator.runtime.aggregate import aggregate_run
    from oracle_db_migration_generator.runtime.worker import offline_plan
    from tests.factories import profile
    desired=source('CREATE TABLE APP.T(ID NUMBER NOT NULL);');observed=actual('CREATE TABLE APP.T(ID NUMBER);')
    root=tmp_path/'run';folder=root/'targets'/'DEMO-TEST'
    written=offline_plan(desired,observed,profile(),folder)
    result={'id':'DEMO-TEST','status':'READY','difference_count':1,'plan_id':written['plan_id'],
            'plan_path':'targets/DEMO-TEST/plan.json','captured_at':None,'error_code':None,'publication':'NOT_REQUESTED'}
    (folder.parent/'DEMO-TEST.result.json').write_text(json.dumps(result),encoding='utf-8')
    with pytest.raises(ValueError,match='RUN_RESULT_PLAN_MISMATCH'): aggregate_run(root)


def test_error_receipt_cannot_impersonate_zero_differences(tmp_path):
    import pytest
    from oracle_db_migration_generator.runtime.aggregate import aggregate_run
    folder=tmp_path/'targets'/'FAILED';folder.mkdir(parents=True)
    (folder/'target-error.json').write_text(json.dumps(dict(id='FAILED',status='NO_CHANGE',difference_count=0,
        plan_id=None,plan_path=None,captured_at=None,error_code='ORA-01031',publication='NOT_REQUESTED')))
    with pytest.raises(ValueError,match='RUN_ERROR_MUST_BE_UNKNOWN'):
        aggregate_run(tmp_path,source_commit='a'*40)


def test_aggregate_records_explicit_jenkins_build_context(tmp_path):
    from oracle_db_migration_generator.runtime.aggregate import aggregate_run
    from oracle_db_migration_generator.runtime.worker import offline_plan
    from tests.factories import profile
    offline_plan(source('CREATE TABLE APP.T(ID NUMBER);'),actual(),profile(),tmp_path/'targets/DEMO-TEST')
    url='https://jenkins.example/job/generator/9/'
    run=aggregate_run(tmp_path,build_number=9,build_url=url)
    assert run['build_url']==url and run['build_number']==9
    assert json.loads((tmp_path/'run.json').read_bytes())['build_url']==url
