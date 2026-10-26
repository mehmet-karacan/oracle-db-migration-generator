import json
import time

import pytest


def connection(**changes):
    return {'name':'Test Oracle','kind':'ORACLE','host':'db.internal','port':1521,
            'service_name':'TEST','username':'APP','password':'synthetic-only-secret',
            'allowed_users':['operator'],**changes}


def test_connection_secrets_are_encrypted_and_never_returned(tmp_path):
    from oracle_db_migration_generator.control.store import ControlStore
    store=ControlStore(tmp_path)
    saved=store.save_connection(connection(),actor='admin')
    assert saved['credential_configured'] is True
    assert 'synthetic-only-secret' not in json.dumps(saved)
    assert 'password' not in saved
    assert store.credentials(saved['id']).password=='synthetic-only-secret'
    assert all(b'synthetic-only-secret' not in p.read_bytes() for p in tmp_path.rglob('*') if p.is_file())
    assert store.connection(saved['id'],actor='operator',role='operator')['id']==saved['id']
    with pytest.raises(PermissionError):store.connection(saved['id'],actor='outsider',role='operator')


@pytest.mark.parametrize('changes',[
    {'host':'db.internal/evil'}, {'port':0}, {'sid':'ALSO'},
    {'kind':'GIT','repository':'https://user:secret@example.test/repo.git'},
    {'kind':'GIT','repository':'file:///secret'},
])
def test_invalid_connection_configuration_is_rejected(tmp_path,changes):
    from oracle_db_migration_generator.control.store import ControlStore
    with pytest.raises(ValueError):ControlStore(tmp_path).save_connection(connection(**changes),actor='admin')


def test_revision_conflict_and_password_preservation(tmp_path):
    from oracle_db_migration_generator.control.store import ControlStore
    store=ControlStore(tmp_path);saved=store.save_connection(connection(),actor='admin')
    updated=store.save_connection({**saved,'name':'Renamed'},actor='admin')
    assert updated['revision']==2
    assert store.credentials(saved['id']).password=='synthetic-only-secret'
    with pytest.raises(ValueError,match='REVISION_CONFLICT'):
        store.save_connection({**saved,'name':'Stale'},actor='admin')


def test_frozen_run_settings_do_not_change_with_new_defaults(tmp_path):
    from oracle_db_migration_generator.control.store import ControlStore
    store=ControlStore(tmp_path)
    c=store.save_connection(connection(),actor='admin')
    p=store.save_profile({'name':'Oracle compare','source':{'kind':'ORACLE','connection_id':c['id'],'schemas':['APP']},
                          'target_ids':[c['id']]},actor='admin')
    run=store.create_run(p['id'],actor='operator',role='operator')
    before=store.run(run['id'])['spec']
    settings=store.settings();store.save_settings({**settings,'capture_timeout_seconds':1200},actor='admin')
    assert store.run(run['id'])['spec']==before
    assert before['settings']['capture_timeout_seconds']==900
    assert before['profile']['source']['kind']=='ORACLE'
    assert 'synthetic-only-secret' not in json.dumps(before)


def test_invalid_settings_and_remap_cannot_be_enabled(tmp_path):
    from oracle_db_migration_generator.control.store import ControlStore
    store=ControlStore(tmp_path)
    for change in ({'capture_timeout_seconds':0},{'max_parallel_jobs':99},{'allow_drop':True},
                   {'notify_to':['someone@example.com']},{'schedule_time':'29:00'}):
        with pytest.raises(ValueError):store.save_settings({**store.settings(),**change},actor='admin')


def test_signed_proxy_auth_and_local_mode_fail_closed():
    from oracle_db_migration_generator.control.auth import authenticate,signature
    stamp=str(int(time.time()));key='synthetic-proxy-key-that-is-long-enough'
    headers={'x-odmg-user':'operator','x-odmg-role':'operator','x-odmg-timestamp':stamp}
    with pytest.raises(PermissionError):authenticate(headers,'10.0.0.1',mode='proxy',key=key)
    headers['x-odmg-signature']=signature(key,'operator','operator',stamp)
    assert authenticate(headers,'10.0.0.1',mode='proxy',key=key)['user']=='operator'
    headers['x-odmg-role']='admin'
    with pytest.raises(PermissionError):authenticate(headers,'10.0.0.1',mode='proxy',key=key)
    with pytest.raises(PermissionError):authenticate({},'10.0.0.1',mode='local',key='')
def test_password_bytes_are_not_trimmed(tmp_path):
    from oracle_db_migration_generator.control.store import ControlStore
    store=ControlStore(tmp_path)
    saved=store.save_connection(connection(password='  synthetic-only-secret  '),actor='admin')
    assert store.credentials(saved['id']).password=='  synthetic-only-secret  '
