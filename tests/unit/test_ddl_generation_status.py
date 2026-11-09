"""Schema Compare üretim sonucunu metadata ve bağımlılık uyarılarından ayırır.

Author: Mehmet KARACAN
Date: 2026-11-09
"""
from copy import deepcopy
import json
import pytest


def sample():
    plan={'operations':[
        {'id':'op-a','decision':'READY','sql':{'path':'objects/a.sql'},'reason_codes':[]},
        {'id':'op-b','decision':'BLOCKED','sql':None,'reason_codes':['DEPENDENCY_UNVERIFIED']},
        {'id':'op-c','decision':'REVIEW_REQUIRED','sql':None,'reason_codes':['SOURCE_INVALID']}],
        'scope':{'inventory':'COMPLETE','ddl':'PARTIAL','dictionary':'COMPLETE'},
        'differences':[{'kind':'UNKNOWN'},{'kind':'CHANGED'}]}
    return plan,[{'id':'T','plan_id':'p','status':'BLOCKED'}]


def test_complete_generation_does_not_hide_partial_comparison_or_warnings():
    from oracle_db_migration_generator.runtime.generation import generation_summary
    plan,targets=sample();before=deepcopy(plan)
    result=generation_summary(targets,{'T':plan},{'T':{'op-b','op-c'}})
    assert result['status']=='SUCCESS' and result['exit_code']==0
    assert result['generated_ddl']==3 and result['missing_ddl']==0
    assert result['metadata_unknown_records']==1
    assert result['incomplete_metadata_targets']==1
    assert result['dependency_warning_operations']==1
    assert result['other_warning_operations']==1
    assert plan==before


def test_one_missing_proposal_remains_unstable():
    from oracle_db_migration_generator.runtime.generation import generation_summary
    plan,targets=sample()
    result=generation_summary(targets,{'T':plan},{'T':{'op-b'}})
    assert result['status']=='UNSTABLE' and result['exit_code']==10
    assert result['missing_ddl']==1


def test_one_failed_target_prevents_success_even_when_other_target_is_complete():
    from oracle_db_migration_generator.runtime.generation import generation_summary
    plan,targets=sample()
    targets.append({'id':'FAILED','plan_id':None,'status':'ERROR'})
    result=generation_summary(targets,{'T':plan},{'T':{'op-b','op-c'}})
    assert result['status']=='FAILURE' and result['exit_code']==20
    assert result['failed_targets']==1


def test_all_targets_must_have_complete_ddl():
    from oracle_db_migration_generator.runtime.generation import generation_summary
    plan,targets=sample();targets.append({'id':'SECOND','plan_id':'p2','status':'BLOCKED'})
    plans={'T':plan,'SECOND':deepcopy(plan)}
    catalog={'T':{'op-b','op-c'},'SECOND':{'op-b','op-c'}}
    assert generation_summary(targets,plans,catalog)['generated_ddl']==6
    catalog['SECOND'].remove('op-c')
    assert generation_summary(targets,plans,catalog)['status']=='UNSTABLE'


def test_no_changes_is_success_without_sql():
    from oracle_db_migration_generator.runtime.generation import generation_summary
    plan,targets=sample();plan.update(operations=[],differences=[])
    result=generation_summary(targets,{'T':plan},{'T':set()})
    assert result['status']=='SUCCESS' and result['generated_ddl']==0


def test_catalog_must_be_known_and_cannot_include_unrelated_operations():
    from oracle_db_migration_generator.runtime.generation import generation_summary
    plan,targets=sample()
    assert generation_summary(targets,{'T':plan},None)['status']=='NOT_VERIFIED'
    with pytest.raises(ValueError,match='PROPOSAL_OPERATION_MISMATCH'):
        generation_summary(targets,{'T':plan},{'T':{'op-a','op-other'}})


def test_aggregate_writes_verified_generation_receipt_and_rejects_sql_corruption(tmp_path):
    from oracle_db_migration_generator.runtime.aggregate import aggregate_run
    from oracle_db_migration_generator.runtime.worker import offline_plan
    from tests.factories import source,actual,profile
    folder=tmp_path/'targets/DEMO-TEST'
    offline_plan(source('CREATE TABLE APP.T(ID NUMBER);'),actual(),profile(),folder)
    run=aggregate_run(tmp_path)
    receipt=json.loads((tmp_path/'ddl-generation.json').read_bytes())
    assert receipt['run_id']==run['run_id'] and receipt['status']=='SUCCESS'
    assert receipt['generated_ddl']==1 and receipt['execution_status']=='NOT_EXECUTED'
    sql=next((folder/'objects').rglob('*.sql'));sql.write_text('broken')
    with pytest.raises(ValueError,match='BUNDLE_INTEGRITY_MISMATCH'):
        aggregate_run(tmp_path)
    assert not (tmp_path/'ddl-generation.json').exists()


def test_reports_separate_generation_and_warning_sections():
    from tests.unit.test_report_views import inputs
    from oracle_db_migration_generator.reporting.view import build_run_view
    from oracle_db_migration_generator.reporting.render import render_email,render_run_reports
    run,plans=inputs();run['status']='PARTIAL'
    for plan in plans.values():
        for op in plan['operations']:
            if op['decision']=='READY':op['sql']={'path':'objects/a.sql'}
    catalog={key:{op['id'] for op in plan['operations'] if op['decision'] in {'BLOCKED','REVIEW_REQUIRED'}} for key,plan in plans.items()}
    view=build_run_view(run,plans,proposal_ids=catalog)
    assert view['display_status']=='DDL Üretimi Tamamlandı'
    assert view['run']['status']=='PARTIAL'
    for raw in (render_email(view),render_run_reports(view)['index.html']):
        html=raw.decode()
        assert 'Metadata Uyarıları' in html and 'Bağımlılık Uyarıları' in html
        assert 'DDL Üretimi Tamamlandı' in html
