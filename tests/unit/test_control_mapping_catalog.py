import copy

import pytest

from test_control_schema_selection import setup_profile


def test_mapping_catalog_is_versioned_project_scoped_and_profiles_freeze_selection(tmp_path):
    store,source,targets,data=setup_profile(tmp_path)
    scope={key:data[key] for key in ('name','source','target_ids','target_mappings')}
    saved=store.save_schema_mapping(scope,actor='shared')
    assert store.list_records('schema_mapping',project_id=source['project_id'])==[saved]
    profile=store.save_profile({**data,'mapping_id':saved['id'],'mapping_revision':saved['revision']},actor='shared')
    run=store.create_run(profile['id'],actor='shared',role='shared')
    revised=copy.deepcopy(saved)
    revised['target_mappings'][targets[0]['id']]=[{'source_schema':'APP','target_schema':'APP'}]
    store.save_schema_mapping(revised,actor='shared')
    assert store.run(run['id'])['spec']['profile']['target_mappings']==data['target_mappings']
    with pytest.raises(ValueError,match='REVISION_CONFLICT'):
        store.save_profile({**profile,'name':'Stale selection'},actor='shared')
    with pytest.raises(ValueError,match='REVISION_CONFLICT'):
        store.save_schema_mapping(saved,actor='shared')


def test_mapping_catalog_rejects_cross_project_and_tampered_profile_scope(tmp_path):
    store,source,targets,data=setup_profile(tmp_path)
    scope={key:data[key] for key in ('name','source','target_ids','target_mappings')}
    saved=store.save_schema_mapping(scope,actor='shared')
    tampered={**data,'mapping_id':saved['id'],'mapping_revision':saved['revision'],'target_ids':[targets[0]['id']],
              'target_mappings':{targets[0]['id']:data['target_mappings'][targets[0]['id']]}}
    with pytest.raises(ValueError,match='SCHEMA_MAPPING_SCOPE_MISMATCH'):
        store.save_profile(tampered,actor='shared')
    other=store.save_project({'name':'Other','code':'OTHER'},actor='shared')
    with pytest.raises(ValueError,match='PROJECT_SCOPE_MISMATCH'):
        store.save_schema_mapping({**scope,'project_id':other['id']},actor='shared')


def test_mapping_catalog_api_auth_and_crud(tmp_path):
    from test_control_api import client
    store,source,targets,data=setup_profile(tmp_path)
    with client(tmp_path) as c:
        assert c.get('/api/schema-mappings').status_code==401
    with client(tmp_path,mode='local') as c:
        scope={key:data[key] for key in ('name','source','target_ids','target_mappings')}
        response=c.post('/api/schema-mappings',json=scope)
        assert response.status_code==200
        saved=response.json()
        assert c.get('/api/schema-mappings?project_id='+source['project_id']).json()==[saved]
        assert 'synthetic-only-secret' not in response.text
        assert c.get('/api/schema-mappings?project_id='+'0'*32).json()==[]


def test_multi_target_round_trip_removal_readd_and_project_boundary(tmp_path):
    from test_control_api import client
    store,source,targets,data=setup_profile(tmp_path)
    scope={key:data[key] for key in ('name','source','target_ids','target_mappings')}
    project=source['project_id'];other=store.save_project({'name':'Other','code':'OTHER'},actor='shared')['id']
    headers={'x-odmg-project':project}
    with client(tmp_path,mode='local') as c:
        first=c.post('/api/schema-mappings',headers=headers,json=scope).json()
        assert first['target_mappings']==data['target_mappings'] and first['revision']==1
        assert c.get('/api/schema-mappings',headers=headers).json()==[first]
        keep,removed=[t['id'] for t in targets]
        second=c.post('/api/schema-mappings',headers=headers,json={**first,'target_ids':[keep],
            'target_mappings':{keep:first['target_mappings'][keep]}}).json()
        assert second['revision']==2 and removed not in second['target_mappings']
        assert c.get('/api/schema-mappings',headers=headers).json()==[second]
        # Re-adding a target without a newly selected pair must not revive its old scope.
        invalid={**second,'target_ids':[keep,removed],'target_mappings':{**second['target_mappings'],removed:[]}}
        assert c.post('/api/schema-mappings',headers=headers,json=invalid).status_code==422
        assert c.get('/api/schema-mappings',headers=headers).json()==[second]
        third=c.post('/api/schema-mappings',headers=headers,json={**second,'target_ids':first['target_ids'],
            'target_mappings':first['target_mappings']}).json()
        assert third['revision']==3 and third['target_mappings']==data['target_mappings']
        assert c.get('/api/schema-mappings',headers=headers).json()==[third]
        assert c.get('/api/schema-mappings',headers={'x-odmg-project':other}).json()==[]
        assert c.post('/api/schema-mappings',headers={'x-odmg-project':other},json={**third,'project_id':other}).status_code==422
        assert c.get('/api/schema-mappings',headers=headers).json()==[third]
