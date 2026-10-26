import copy
from oracle_db_migration_generator.control.results import project_plan,object_detail,object_page
from test_control_results import fixture_plan,completed_run


def structured_view():
    plan,key=fixture_plan();base=plan['differences'][0];rows=[]
    for name in ('FK_CUSTOMER','FK_ORDER'):
        for field in ('exists','kind','columns','reference','enabled','validation','deferrable','initially','delete_rule','rely','condition'):
            value=True if field=='exists' else '[["code","FOREIGN"],["code","KEY"]]' if field=='kind' else None
            rows.append({**copy.deepcopy(base),'id':name+'-'+field,'property_path':f'/constraints/{name}/{field}','kind':'MISSING','after':{'state':'KNOWN','value':value,'evidence_ids':[]},'before':{'state':'ABSENT','value':None,'evidence_ids':[]}})
    plan['differences']=rows;plan['counts']['observed_differences']=22;plan['operations'][0]['change_ids']=[r['id'] for r in rows]
    return project_plan(plan),key


def test_grouped_detail_keeps_complete_constraints_and_summary_across_pages(tmp_path):
    view,key=structured_view();store,id,target,_,_=completed_run(tmp_path)
    first=object_detail(view,store.run(id),target,key,category='all',page=1,size=1,operation_page=1,grouped=True)
    second=object_detail(view,store.run(id),target,key,category='all',page=2,size=1,operation_page=1,grouped=True)
    assert first['group_total']==2 and first['total']==22 and first['summary']['group_count']==2
    assert first['summary']['items']==[{'entity_type':'FOREIGN_KEY','status':'MISSING','count':2}]
    assert len(first['groups'])==len(second['groups'])==1
    assert len(first['groups'][0]['rows'])==len(second['groups'][0]['rows'])==11
    assert first['groups'][0]['name']!=second['groups'][0]['name']
    assert first['groups'][0]['operation_ids']==[view['operations'][0]['id']]


def test_missing_property_does_not_prove_entire_column_missing(tmp_path):
    view,key=structured_view();store,id,target,_,_=completed_run(tmp_path)
    view['differences']=[{**view['differences'][0],'property_path':'/columns/TITLE/default'},
                         {**view['differences'][1],'id':'unknown','property_path':'/columns/TITLE/nullable','kind':'UNKNOWN','source':{'state':'UNKNOWN','value':None},'target':{'state':'KNOWN','value':None}}]
    view['operations'][0]['change_ids']=[r['id'] for r in view['differences']]
    result=object_detail(view,store.run(id),target,key,category='all',page=1,size=25,operation_page=1,grouped=True)
    group=result['groups'][0]
    assert group['status']=='UNKNOWN' and group['name']=='TITLE'
    assert result['summary']['unknown_count']==1 and result['summary']['object_presence'] is None


def test_difference_filter_is_applied_before_pagination_and_separate_from_ddl():
    view,_=structured_view()
    missing=object_page(view,page=1,size=25,search='',object_type='TABLE',difference_kind='MISSING')
    assert missing['total']==1 and missing['rows'][0]['difference_kinds']==['MISSING']
    assert missing['rows'][0]['decisions']==['READY']
    assert object_page(view,page=1,size=25,search='',object_type='',difference_kind='CHANGED')['total']==0

def test_structure_api_validates_filter_and_returns_complete_groups(tmp_path):
    from fastapi.testclient import TestClient
    from oracle_db_migration_generator.control.api import create_app
    from oracle_db_migration_generator.control.results import import_view
    store,id,target,plan,key=completed_run(tmp_path);view,_=structured_view()
    view['target_id']=target
    store.update_run(id,external=None,executor='LOCAL',targets=[{'id':target,'plan_id':plan['plan_id']}])
    import_view(store,id,target,view)
    with TestClient(create_app(tmp_path,mode='local',start_workers=False)) as client:
        base=f'/api/runs/{id}/results/objects'
        assert client.get(base,params={'target_id':target,'difference_kind':'NO_CHANGE'}).status_code==422
        result=client.get(base+'/'+key,params={'target_id':target,'grouped':True,'operation_group':'/constraints/FK_CUSTOMER'}).json()
        assert result['group_total']==2 and len(result['groups'][0]['rows'])==11
        assert result['operation_total']==1
        assert client.get(base+'/'+key,params={'target_id':target,'operation_group':'/constraints/OTHER'}).status_code==404
