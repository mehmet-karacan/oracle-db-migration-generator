import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

from test_control_store import connection


def setup_runs(tmp_path,count=1):
    from oracle_db_migration_generator.control.store import ControlStore
    store=ControlStore(tmp_path);c=store.save_connection(connection(),actor='admin')
    p=store.save_profile({'name':'Queue','source':{'kind':'ORACLE','connection_id':c['id'],'schemas':['APP']},'target_ids':[c['id']]},actor='admin')
    runs=[store.create_run(p['id'],actor='admin',role='admin') for _ in range(count)]
    return store,runs


def test_scheduler_reservation_is_atomic_and_backlog_is_not_limited_to_200(tmp_path):
    store,runs=setup_runs(tmp_path,202)
    with ThreadPoolExecutor(max_workers=2) as pool:
        reservations=list(pool.map(lambda _:store.reserve_next_run(1),range(2)))
    reserved=[r for r in reservations if r]
    assert len(reserved)==1 and reserved[0]['id']==runs[0]['id']
    assert len(store.scheduler_runs())==202


def test_running_worker_without_pid_is_recovered_after_claim_timeout(tmp_path):
    from oracle_db_migration_generator.control.queue import LocalQueue
    store,runs=setup_runs(tmp_path)
    store.update_run(runs[0]['id'],status='RUNNING',claimed=True,claimed_at='2000-01-01T00:00:00+00:00')
    LocalQueue(store).tick()
    assert store.run(runs[0]['id'])['error_code']=='WORKER_INTERRUPTED'


def test_non_default_remote_branch_is_resolved_without_a_checkout(tmp_path):
    from oracle_db_migration_generator.control.runner import resolve_git_revision
    repo=tmp_path/'repo';repo.mkdir()
    subprocess.run(['git','-C',str(repo),'init'],check=True,capture_output=True)
    (repo/'sample.txt').write_text('fixture',encoding='utf-8')
    for args in (['add','.'],['-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','fixture']):
        subprocess.run(['git','-C',str(repo),*args],check=True,capture_output=True)
    sha=subprocess.run(['git','-C',str(repo),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
    subprocess.run(['git','-C',str(repo),'update-ref','refs/remotes/origin/release/foo',sha],check=True,capture_output=True)
    assert resolve_git_revision(repo,'release/foo').commit==sha
    subprocess.run(['git','-C',str(repo),'tag','release/foo'],check=True,capture_output=True)
    import pytest
    with pytest.raises(ValueError,match='GIT_REF_AMBIGUOUS'):resolve_git_revision(repo,'release/foo')


def test_connection_test_uses_isolated_process_and_frozen_budgets(tmp_path,monkeypatch):
    from oracle_db_migration_generator.control.runner import isolated_connection_test
    import subprocess
    store,_=setup_runs(tmp_path);c=store.list_records('connection')[0]
    seen={}
    def launch(args,**kwargs):
        seen.update(args=args,kwargs=kwargs)
        return subprocess.CompletedProcess(args,0,stdout=json.dumps({'status':'CONNECTED'}).encode(),stderr=b'')
    monkeypatch.setattr(subprocess,'run',launch)
    assert isolated_connection_test(store,c,schemas=['APP'])['status']=='CONNECTED'
    assert 'oracle_db_migration_generator.control.connection_probe' in seen['args']
    assert c['id'] in seen['args'] and 'synthetic-only-secret' not in repr(seen['args'])
    assert json.loads(seen['kwargs']['input'])['settings']['connect_timeout_seconds']==8


def test_external_vault_key_does_not_create_a_local_key_file(tmp_path,monkeypatch):
    from cryptography.fernet import Fernet
    from oracle_db_migration_generator.control.store import ControlStore
    monkeypatch.setenv('ODMG_UI_VAULT_KEY',Fernet.generate_key().decode())
    store=ControlStore(tmp_path);c=store.save_connection(connection(),actor='admin')
    assert not (tmp_path/'vault.key').exists()
    assert ControlStore(tmp_path).credentials(c['id']).password=='synthetic-only-secret'


def test_external_workers_also_obey_global_job_capacity(tmp_path):
    store,runs=setup_runs(tmp_path,2)
    assert store.begin_run(runs[0]['id'])
    assert not store.begin_run(runs[1]['id'])
    assert store.run(runs[1]['id'])['status']=='QUEUED'
    store.update_run(runs[0]['id'],status='COMPLETE')
    assert store.begin_run(runs[1]['id'])
