import copy

import pytest

from test_control_store import connection


def setup_profile(tmp_path):
    from oracle_db_migration_generator.control.store import ControlStore
    store=ControlStore(tmp_path)
    source=store.save_connection(connection(username='READER'),actor='admin')
    targets=[store.save_connection(connection(name=name,username='OTHER_READER'),actor='admin') for name in ('PROD','UAT')]
    data={'name':'Explicit schemas','source':{'kind':'ORACLE','connection_id':source['id'],'schemas':['APP','TTBP']},
          'target_ids':[t['id'] for t in targets],
          'target_mappings':{targets[0]['id']:[{'source_schema':'TTBP','target_schema':'TTBP'}],
                             targets[1]['id']:[{'source_schema':'APP','target_schema':'APP'}]}}
    return store,source,targets,data


def test_explicit_schema_selection_is_frozen_without_changing_login(tmp_path):
    store,source,targets,data=setup_profile(tmp_path)
    saved=store.save_profile(data,actor='admin')
    run=store.create_run(saved['id'],actor='admin',role='admin')
    assert run['spec']['profile']['target_mappings']==data['target_mappings']
    assert store.credentials(source['id']).username=='READER'
    changed=copy.deepcopy(saved)
    changed['target_mappings'][targets[0]['id']]=[{'source_schema':'APP','target_schema':'APP'}]
    store.save_profile(changed,actor='admin')
    assert store.run(run['id'])['spec']['profile']['target_mappings']==data['target_mappings']


@pytest.mark.parametrize('variant',['empty','missing_target','outside_target','outside_source','duplicate','remap'])
def test_invalid_explicit_schema_selection_is_rejected(tmp_path,variant):
    store,source,targets,data=setup_profile(tmp_path)
    first=targets[0]['id']
    if variant=='empty':data['target_mappings'][first]=[]
    if variant=='missing_target':data['target_mappings'].pop(first)
    if variant=='outside_target':data['target_mappings'][source['id']]=data['target_mappings'][first]
    if variant=='outside_source':data['target_mappings'][first]=[{'source_schema':'OTHER','target_schema':'OTHER'}]
    if variant=='duplicate':data['target_mappings'][first]*=2
    if variant=='remap':data['target_mappings'][first]=[{'source_schema':'APP','target_schema':'TTBP'}]
    with pytest.raises(ValueError):store.save_profile(data,actor='admin')


def test_runner_builds_explicit_pairs_and_uses_login_as_catalog_reader(tmp_path):
    from oracle_db_migration_generator.control.runner import target_config
    store,source,targets,data=setup_profile(tmp_path)
    mappings=data['target_mappings'][targets[0]['id']]
    config=target_config(targets[0],['APP','TTBP'],store.settings(),mappings=mappings,username='OTHER_READER')
    assert [(m.source_schema,m.target_schema,m.metadata_reader) for m in config.schema_mappings]==[('TTBP','TTBP','OTHER_READER')]
    own=target_config(source,['READER'],store.settings(),username='READER')
    assert own.schema_mappings[0].metadata_reader is None


def test_default_explicit_scope_keeps_existing_jenkins_fingerprint(tmp_path):
    from oracle_db_migration_generator.control.jenkins_browser import spec_fingerprint
    store,source,targets,data=setup_profile(tmp_path)
    data.pop('target_mappings')
    p=store.save_profile(data,actor='admin')
    spec=store.run_spec(p['id'],actor='admin',role='admin')
    legacy=copy.deepcopy(spec)
    legacy['profile'].pop('target_mappings',None)
    explicit=copy.deepcopy(legacy)
    explicit['profile']['target_mappings']={t['id']:[{'source_schema':s,'target_schema':s} for s in ['TTBP','APP']] for t in targets}
    assert spec_fingerprint(explicit)==spec_fingerprint(legacy)
    explicit['profile']['target_mappings'][targets[0]['id']].pop()
    assert spec_fingerprint(explicit)!=spec_fingerprint(legacy)


def test_profile_api_requires_explicit_pairs_for_new_saves(tmp_path):
    from test_control_api import client
    store,source,targets,data=setup_profile(tmp_path)
    with client(tmp_path,mode='local') as c:
        omitted={k:v for k,v in data.items() if k!='target_mappings'}
        response=c.post('/api/profiles',json=omitted)
        assert response.status_code==422
        assert response.json()['detail']=='TARGET_SCHEMA_SCOPE_REQUIRED'
        assert c.post('/api/profiles',json=data).status_code==200


@pytest.mark.parametrize('roles',[[('SELECT_CATALOG_ROLE',)],[]])
def test_cross_schema_connection_test_verifies_catalog_access(tmp_path,roles):
    from oracle_db_migration_generator.control.runner import test_connection
    from test_catalog_reader import RecordingCursor
    store,source,targets,data=setup_profile(tmp_path)
    cursor=RecordingCursor([('READER',),roles,[('TTBP',)],[],[]])
    class Database:
        closed=False
        rolled_back=False
        def cursor(self):return cursor
        def rollback(self):self.rolled_back=True
        def close(self):self.closed=True
    db=Database()
    if roles:
        result=test_connection(store,source,schemas=['TTBP'],connect=lambda *_:db)
        assert result['schemas']==('TTBP',) and result['inventory_access_verified']
        assert not result['ddl_access_verified']
        assert 'dba_objects' in cursor.calls[-1][0]
    else:
        with pytest.raises(ValueError,match='CATALOG_READER_ROLE_REQUIRED'):
            test_connection(store,source,schemas=['TTBP'],connect=lambda *_:db)
        assert len(cursor.calls)==3
        assert cursor.calls[0][0]=='SET TRANSACTION READ ONLY'
    assert db.closed and db.rolled_back and cursor.closed


def test_execute_run_routes_source_and_each_target_schema_independently(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from oracle_db_migration_generator.control import runner
    store,source,targets,data=setup_profile(tmp_path)
    p=store.save_profile(data,actor='admin')
    run=store.create_run(p['id'],actor='admin',role='admin')
    seen=[]
    def capture(config,*args,**kwargs):
        seen.append(('source',config))
        return SimpleNamespace(snapshot=SimpleNamespace(source_commit=None,source_origin=None))
    def compare(snapshot,config,*args,**kwargs):
        seen.append(('target',config))
        return {'id':config.id,'status':'NO_CHANGE'}
    monkeypatch.setattr(runner,'save_source',lambda *args:None)
    monkeypatch.setattr(runner,'run_target',compare)
    monkeypatch.setattr(runner,'aggregate_run',lambda *args,**kwargs:{'status':'COMPLETE','source_commit':None})
    runner.execute_run(store,run['id'],source_collector=capture)
    assert store.run(run['id'])['status']=='COMPLETE'
    assert [(side,[m.target_schema for m in config.schema_mappings]) for side,config in seen]==[
        ('source',['APP','TTBP']),('target',['TTBP']),('target',['APP'])]
    assert all(m.metadata_reader==('READER' if side=='source' else 'OTHER_READER')
               for side,config in seen for m in config.schema_mappings)
