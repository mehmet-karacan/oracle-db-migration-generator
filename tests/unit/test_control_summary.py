import hashlib
import json
import pytest
from oracle_db_migration_generator.control.results import import_view,project_plan
from test_control_results import completed_run


def test_summary_preserves_unknowns_and_reads_real_difference_counts(tmp_path):
    from oracle_db_migration_generator.control.summary import run_summary,import_scan
    store,id,target,plan,_=completed_run(tmp_path)
    result=run_summary(store,store.run(id))
    assert result['source_total'] is None and result['counts'] is None
    import_view(store,id,target,project_plan(plan))
    result=run_summary(store,store.run(id))
    assert result['source_total'] is None
    assert result['counts']['observed_differences']==3 and result['unknown_count']==1
    assert result['verified_difference_count']==2
    summary={'schema_version':'scan-summary/1.0','plan_id':plan['plan_id'],'source_digest':'a'*64,
             'target_digest':'b'*64,'target_id':plan['target']['id'],
             'source':{'by_schema':{'APP':{'TABLE':5,'COMMENT':12}},'inventory':'COMPLETE','excluded':2},
             'target':{'by_schema':{'APP':{'TABLE':4}},'inventory':'PARTIAL','excluded':0}}
    raw=json.dumps(summary).encode()
    manifest={'plan_id':plan['plan_id'],'files':[{'path':'scan-summary.json','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}]}
    import_scan(store,id,target,raw,manifest)
    result=run_summary(store,store.run(id))
    assert result['source_total']==5 and result['source_inventory']=='COMPLETE'
    assert result['source_types']=={'TABLE':5}
    with pytest.raises(ValueError):import_scan(store,id,target,raw+b' ',manifest)
    summary['source']['by_schema']['APP']['TABLE']=6
    changed=json.dumps(summary).encode()
    manifest['files'][0].update(bytes=len(changed),sha256=hashlib.sha256(changed).hexdigest())
    with pytest.raises(ValueError,match='SCAN_SUMMARY_IMMUTABLE'):import_scan(store,id,target,changed,manifest)
