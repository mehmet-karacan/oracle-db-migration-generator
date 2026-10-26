import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from oracle_db_migration_generator.control.store import ControlStore
from test_control_store import connection


def fixture_plan():
    plan=json.loads(Path('examples/plan.example.json').read_bytes())
    key=plan['differences'][0]['object_key']
    base=plan['differences'][0]
    plan['differences']=[{**copy.deepcopy(base),'id':'change-title-length','property_path':'/columns/TITLE/length'},
        {**copy.deepcopy(base),'id':'unknown-null','property_path':'/columns/TITLE/default','kind':'UNKNOWN',
         'before':{'state':'KNOWN','value':None,'evidence_ids':[]},'after':{'state':'UNKNOWN','value':None,'evidence_ids':[]}},
        {**copy.deepcopy(base),'id':'body','property_path':'/definition','before':{'state':'KNOWN','value':'SECRET_SQL_BODY','evidence_ids':[]},'after':{'state':'KNOWN','value':'NEW_SECRET_BODY','evidence_ids':[]}}]
    plan['counts']['observed_differences']=3
    plan['operations'][0]['change_ids']=['change-title-length','unknown-null','body']
    plan['operations'][0]['sql']={'path':'ddl/001-title.sql','sha256':'a'*64}
    return plan,key


def completed_run(tmp_path):
    s=ControlStore(tmp_path);c=s.save_connection(connection(),actor='shared')
    p=s.save_profile({'name':'Compare','source':{'kind':'ORACLE','connection_id':c['id'],'schemas':['APP']},'target_ids':[c['id']]},actor='shared')
    run=s.create_run(p['id'],actor='shared',role='shared')
    plan,key=fixture_plan()
    plan['synthetic']=False
    s.update_run(run['id'],status='PARTIAL',stage='FINISHED',source_commit=plan['source']['commit_sha'],
        targets=[{'id':plan['target']['id'],'plan_id':plan['plan_id'],'status':'BLOCKED','difference_count':None}],
        external={'mode':'BROWSER_HANDOFF','target_map':{c['id']:plan['target']['id']},'build_url':'https://jenkins.example.test/job/compare/55/'})
    return s,run['id'],c['id'],plan,key


def test_projection_retains_direction_states_and_links_but_omits_sql_bodies():
    from oracle_db_migration_generator.control.results import project_plan
    plan,key=fixture_plan();original=copy.deepcopy(plan)
    view=project_plan(plan)
    assert plan==original
    row=view['differences'][0]
    assert row['source']['value']==80 and row['target']['value']==40
    assert row['object_key']==key
    assert view['differences'][1]['source']['state']=='UNKNOWN'
    assert view['differences'][1]['target']=={'state':'KNOWN','value':None,'omitted':False}
    assert view['differences'][2]['source']['omitted'] is True
    assert 'SECRET' not in json.dumps(view)
    assert view['operations'][0]['change_ids']==plan['operations'][0]['change_ids']
    assert view['operations'][0]['sql_path']=='ddl/001-title.sql'


def test_import_is_frozen_and_rejects_wrong_plan_target_or_source(tmp_path):
    from oracle_db_migration_generator.control.results import project_plan,import_view
    s,id,target,plan,key=completed_run(tmp_path)
    view=project_plan(plan)
    for change in [{'plan_id':'b'*64},{'target_id':'WRONG'},{'source_commit':'c'*40}]:
        with pytest.raises(ValueError):import_view(s,id,target,{**view,**change})
    import_view(s,id,target,view)
    import_view(s,id,target,view)
    changed=copy.deepcopy(view);changed['differences'][0]['source']['value']=999
    with pytest.raises(ValueError,match='RESULT_VIEW_IMMUTABLE'):import_view(s,id,target,changed)
    unsafe=copy.deepcopy(view);unsafe['operations'][0]['sql_path']='../../vault.key'
    with pytest.raises(ValueError):import_view(s,id,target,unsafe)


def test_results_api_groups_and_paginates_saved_evidence_without_oracle(tmp_path):
    from oracle_db_migration_generator.control.api import create_app
    from oracle_db_migration_generator.control.results import project_plan,import_view
    s,id,target,plan,key=completed_run(tmp_path)
    with TestClient(create_app(tmp_path,mode='local',start_workers=False),client=('127.0.0.1',1234)) as client:
        base=f'/api/runs/{id}/results/objects'
        missing=client.get(base,params={'target_id':target}).json()
        assert missing['available'] is False and missing['total'] is None
        import_view(s,id,target,project_plan(plan))
        response=client.get(base,params={'target_id':target,'object_type':'TABLE'}).json()
        assert response['available'] is True and response['total']==1
        assert response['unknown_count']==1 and response['observed_difference_count']==2
        assert response['rows'][0]['name']=='DEMO_NOTE' and response['rows'][0]['difference_count']==3
        detail=client.get(base+'/'+key,params={'target_id':target,'section':'columns','size':25}).json()
        assert detail['total']==2 and len(detail['rows'])==2
        assert detail['operations'][0]['sql_url'].endswith('/55/artifact/output/runs/build-55/targets/DEMO-TEST/ddl/001-title.sql/*view*/')
        assert client.get(base,params={'target_id':target,'search':'absent'}).json()['total']==0
        assert client.get(base,params={'target_id':'0'*32}).status_code==404
        assert client.get(base+'/'+key,params={'target_id':target,'page':0}).status_code==422
        assert client.get(base,params={'target_id':target,'object_type':'BOGUS'}).status_code==422


def test_result_paging_keeps_all_fields_and_absence_states(tmp_path):
    from oracle_db_migration_generator.control.results import project_plan,object_page,object_detail
    s,id,target,plan,key=completed_run(tmp_path)
    base=plan['differences'][0]
    plan['differences']=[{**copy.deepcopy(base),'id':f'change-{i}','property_path':f'/columns/C{i}/length'} for i in range(61)]
    plan['differences'][0]['after']={'state':'ABSENT','value':None,'evidence_ids':[]}
    plan['differences'][1]['after']={'state':'NOT_APPLICABLE','value':None,'evidence_ids':[]}
    plan['operations'][0]['change_ids']=[r['id'] for r in plan['differences']]
    plan['counts']['observed_differences']=61
    view=project_plan(plan)
    assert object_page(view,page=1,size=25,search='',object_type='TABLE')['rows'][0]['difference_count']==61
    pages=[object_detail(view,s.run(id),target,key,category='columns',page=n,size=25,operation_page=1) for n in (1,2,3)]
    assert [len(page['rows']) for page in pages]==[25,25,11]
    assert len({r['id'] for page in pages for r in page['rows']})==61
    assert pages[0]['rows'][0]['source']['state']=='ABSENT'
    assert pages[0]['rows'][1]['source']['state']=='NOT_APPLICABLE'


def test_malformed_views_are_rejected_and_api_requires_identity(tmp_path):
    from oracle_db_migration_generator.control.api import create_app
    from oracle_db_migration_generator.control.results import project_plan,import_view
    s,id,target,plan,key=completed_run(tmp_path);view=project_plan(plan)
    bad=copy.deepcopy(view);bad['differences'].append(bad['differences'][0])
    with pytest.raises(ValueError):import_view(s,id,target,bad)
    bad=copy.deepcopy(view);bad['operations'][0]['change_ids']=['not-a-recorded-change']
    with pytest.raises(ValueError):import_view(s,id,target,bad)
    with pytest.raises(ValueError):import_view(s,id,target,{**view,'synthetic':True})
    with TestClient(create_app(tmp_path,start_workers=False)) as client:
        assert client.get(f'/api/runs/{id}/results/objects',params={'target_id':target}).status_code==401
        assert client.get(f'/api/runs/{id}/results/objects/{key}',params={'target_id':target}).status_code==401


def test_comment_display_name_is_searchable_without_changing_its_canonical_key(tmp_path):
    from oracle_db_migration_generator.control.results import project_plan,object_page,object_detail,object_key
    s,id,target,plan,key=completed_run(tmp_path)
    identity={**plan['operations'][0]['object'],'object_type':'COMMENT','name':'S_123','display_name':'APP.CUSTOMER.TITLE'}
    key=object_key(identity);plan['operations'][0]['object']=identity
    for row in plan['differences']:row['object_key']=key
    view=project_plan(plan)
    page=object_page(view,page=1,size=25,search='CUSTOMER.TITLE',object_type='COMMENT')
    assert page['total']==1
    assert page['rows'][0]['display_name']=='APP.CUSTOMER.TITLE' and page['rows'][0]['key']==key
    detail=object_detail(view,s.run(id),target,key,category='all',page=1,size=50,operation_page=1)
    assert detail['display_name']=='APP.CUSTOMER.TITLE' and detail['key']==key
