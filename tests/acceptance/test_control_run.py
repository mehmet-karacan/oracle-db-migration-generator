from pathlib import Path
import json
import subprocess

from oracle_db_migration_generator.control.store import ControlStore
from oracle_db_migration_generator.control.runner import execute_run
from oracle_db_migration_generator.config.credentials import Credentials
from oracle_db_migration_generator.oracle.collector import collect_target


def test_git_control_run_uses_real_parser_planner_and_sql(tmp_path):
    # Network is the only replaced boundary; all Git bytes and SQL are real.
    import importlib.util
    helper=importlib.util.spec_from_file_location('control_test_collector',Path(__file__).resolve().parents[1]/'unit/test_collector.py')
    module=importlib.util.module_from_spec(helper);helper.loader.exec_module(module)
    FakeConnection=module.FakeConnection
    repo=tmp_path/'fixture';repo.mkdir()
    sql=repo/'app/tables/UI_DEMO/ddl.sql';sql.parent.mkdir(parents=True)
    sql.write_text('CREATE TABLE APP.UI_DEMO (ID NUMBER);\n',encoding='utf-8')
    for args in (['init'],['add','.'],['-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','fixture']):
        subprocess.run(['git','-C',str(repo),*args],check=True,capture_output=True)
    sha=subprocess.run(['git','-C',str(repo),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
    store=ControlStore(tmp_path/'state')
    source=store.save_connection({'kind':'GIT','name':'Fixture Git','repository':'https://example.invalid/fixture.git'},actor='admin')
    target=store.save_connection({'kind':'ORACLE','name':'Test target','host':'oracle.invalid','service_name':'TEST',
                                 'username':'APP','password':'synthetic-secret'},actor='admin')
    profile=store.save_profile({'name':'Git test','source':{'kind':'GIT','connection_id':source['id'],'schemas':['APP'],'ref':sha},
                               'target_ids':[target['id']]},actor='admin')
    def capture(config,credentials,profile,**kwargs):
        return collect_target(config,credentials,profile,connect=lambda *_:FakeConnection(),**kwargs)
    run=store.create_run(profile['id'],actor='admin',role='admin')
    execute_run(store,run['id'],checkout=lambda *a:repo,target_collector=capture)
    result=store.run(run['id'])
    assert result['status'] in {'COMPLETE','PARTIAL'},result
    assert result['source_commit']==sha and result['targets'][0]['plan_id']
    root=store.root/'runs'/run['id']
    files=list((root/'targets').rglob('objects/**/*.sql'))
    assert any(b'CREATE TABLE APP.UI_DEMO' in p.read_bytes() for p in files)
    from oracle_db_migration_generator.artifacts.bundle import verify_bundle
    verify_bundle(root/'targets'/target['id'])
    assert 'synthetic-secret' not in (root/'run.json').read_text(encoding='utf-8')
    again=store.create_run(profile['id'],actor='admin',role='admin')
    execute_run(store,again['id'],checkout=lambda *a:repo,target_collector=capture)
    assert store.run(again['id'])['source_performance']['cache_status']=='HIT_VERIFIED'
