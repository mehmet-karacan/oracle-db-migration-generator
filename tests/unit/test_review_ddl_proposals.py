"""Şema Karşılaştırma inceleme kayıtlarının SQL önerilerini sınar.

Sentetik şemalar kullanılır ve veritabanına bağlanılmaz.

Author: Mehmet KARACAN
Date: 2026-11-02
"""

from oracle_db_migration_generator.artifacts.bundle import verify_bundle, write_bundle
from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
from oracle_db_migration_generator.model.snapshot import KnownValue
from types import SimpleNamespace
from tests.factories import actual, profile, source
from tests.unit.test_compiled_routine_proof import fixture, planned
from tests.unit.test_rules import plan


def test_dynamic_routine_has_separate_ddl_proposal_and_reason(tmp_path):
    desired, target, caps = fixture(
        "CREATE PROCEDURE APP.P IS BEGIN EXECUTE IMMEDIATE 'delete from APP.T'; END;"
    )
    plan = planned(desired, target, caps)
    operation = next(op for op in plan.operations if op.identity.name.effective_name == 'P')
    assert operation.decision == 'REVIEW_REQUIRED'
    assert operation.intent is None and operation.proposal is not None
    folder = tmp_path / 'bundle'
    write_bundle(plan, folder)
    proposal = next(folder.glob('proposals/**/op-*.sql'))
    text = proposal.read_text(encoding='utf-8')
    assert 'CREATE OR REPLACE PROCEDURE APP.P' in text
    assert 'Dinamik SQL' in text
    assert proposal.relative_to(folder).as_posix() in (folder / 'index.html').read_text(encoding='utf-8')
    aggregate = folder / 'partial-ready.sql'
    assert not aggregate.exists() or proposal.relative_to(folder).as_posix() not in aggregate.read_text(encoding='utf-8')
    assert verify_bundle(folder)['status'] == 'VERIFIED'


def test_namespace_conflict_keeps_source_ddl_as_blocked_proposal(tmp_path):
    result=plan('CREATE FUNCTION APP.COLLISION RETURN NUMBER IS BEGIN RETURN 1; END;',
                'CREATE TABLE APP.COLLISION(ID NUMBER);')
    function=next(op for op in result.operations if op.identity.object_type=='FUNCTION')
    assert function.decision=='BLOCKED'
    assert function.intent is None and function.proposal is not None
    folder=tmp_path/'bundle'
    write_bundle(result,folder)
    text=next(folder.glob('proposals/**/op-*.sql')).read_text(encoding='utf-8')
    assert 'CREATE OR REPLACE FUNCTION APP.COLLISION' in text
    assert 'Kaynakta FUNCTION, hedefte aynı adlı TABLE var' in text
    assert '-- Gerekçe ' in text
    report=(folder/'index.html').read_text(encoding='utf-8')
    assert 'DDL üretildi' in report
    assert 'Üretilen DDL</span><strong>1</strong>' in report
    aggregate=folder/'partial-ready.sql'
    assert not aggregate.exists() or 'proposals/' not in aggregate.read_text(encoding='utf-8')
    assert verify_bundle(folder)['status']=='VERIFIED'


def test_email_counts_generated_conflict_sql_without_missing_ddl(tmp_path):
    from oracle_db_migration_generator.reporting.view import build_run_view
    from oracle_db_migration_generator.reporting.render import render_email
    result=plan('CREATE FUNCTION APP.COLLISION RETURN NUMBER IS BEGIN RETURN 1; END;',
                'CREATE TABLE APP.COLLISION(ID NUMBER);')
    blocked=next(op for op in result.operations if op.identity.object_type=='FUNCTION')
    target_id=result.target['id']
    run={'run_id':'draft','source_commit':'a'*40,'status':'PARTIAL',
         'started_at':'2026-11-02T08:00:00Z','finished_at':'2026-11-02T08:01:00Z',
         'targets':[{'id':target_id,'status':'BLOCKED','difference_count':1,
                     'plan_id':result.plan_id,'plan_path':f'targets/{target_id}/plan.json','error_code':None}]}
    document=result.to_dict()
    document['target']['name']='PROD - APP'
    view=build_run_view(run,{target_id:document},proposal_ids={target_id:{blocked.operation_id}})
    assert view['metrics'][2]['value']=='1'
    assert view['metrics'][4]['value']=='0'
    assert view['important_objects'][0]['display_status']=='DDL üretildi'
    html=render_email(view,preview=True).decode('utf-8')
    assert 'Kaynakta fonksiyon, hedefte aynı adlı tablo var.' in html
    assert 'DDL Dosyası Eksik' in html
    assert 'Ayrı DDL' not in html
    assert 'Taranan Nesne' in html
    assert 'PROD - APP (APP)' not in html
    assert 'İşlem</th>' not in html


def test_run_and_jenkins_mail_read_proposal_files(tmp_path):
    from oracle_db_migration_generator.runtime.aggregate import aggregate_run
    from tools.jenkins_notification import write_notification
    result=plan('CREATE FUNCTION APP.COLLISION RETURN NUMBER IS BEGIN RETURN 1; END;',
                'CREATE TABLE APP.COLLISION(ID NUMBER);')
    target_id=result.target['id']
    write_bundle(result,tmp_path/'targets'/target_id)
    job='https://jenkins.example/job/generator/'
    run=aggregate_run(tmp_path,source_commit=result.source['commit_sha'],
                      build_number=7,build_url=job+'7/')
    body=write_notification(tmp_path,run,job+'7/',job).read_text(encoding='utf-8')
    assert 'DDL Dosyası Eksik' in body
    assert 'Kaynakta fonksiyon, hedefte aynı adlı tablo var.' in body
    assert 'Üretilemeyen DDL' not in body


def test_namespace_conflict_does_not_add_replace_to_table(tmp_path):
    result=plan('CREATE TABLE APP.COLLISION(ID NUMBER);',
                'CREATE FUNCTION APP.COLLISION RETURN NUMBER IS BEGIN RETURN 1; END;')
    table=next(op for op in result.operations if op.identity.object_type=='TABLE')
    assert table.decision=='BLOCKED' and table.proposal is not None
    folder=tmp_path/'bundle'
    write_bundle(result,folder)
    text=next(folder.glob('proposals/**/op-*.sql')).read_text(encoding='utf-8')
    assert 'CREATE TABLE APP.COLLISION' in text
    assert 'CREATE OR REPLACE TABLE' not in text


def test_existing_sequence_proposes_alter_without_counter_reset(tmp_path):
    selected = profile()
    desired = source('CREATE SEQUENCE APP.S INCREMENT BY 1 MINVALUE 1 MAXVALUE 999999 CACHE 20;')
    target = actual('CREATE SEQUENCE APP.S INCREMENT BY 1 MINVALUE 1 MAXVALUE 99999 NOCACHE;')
    plan = plan_target(compare_snapshots(desired, target, selected.policy),
                       PlanningContext(desired, target, selected, 'Sequence'))
    operation = next(op for op in plan.operations if op.identity.object_type == 'SEQUENCE')
    assert operation.decision == 'REVIEW_REQUIRED'
    assert operation.intent is None and operation.proposal is not None
    assert 'ALTER SEQUENCE önerisi ayrı dosyada hazırlandı' in operation.reason_tr
    assert 'henüz tanımlı değil' not in operation.reason_tr
    folder = tmp_path / 'bundle'
    write_bundle(plan, folder)
    proposal = next(folder.glob('proposals/**/op-*.sql')).read_text(encoding='utf-8')
    assert 'ALTER SEQUENCE "APP"."S" MAXVALUE 999999 CACHE 20;' in proposal
    assert 'START WITH' not in proposal
    assert 'CACHE 20' in proposal


def test_trigger_export_enable_sidecar_is_not_duplicated_in_proposal():
    from oracle_db_migration_generator.planning.object_rules import review_source_statement
    raw=(b'CREATE TRIGGER APP.TRG BEFORE INSERT ON APP.T FOR EACH ROW '
         b'BEGIN :NEW.ID := 1; END;\nALTER TRIGGER "APP"."TRG" ENABLE')
    desired=source('CREATE TABLE APP.T(ID NUMBER); '+raw.decode('utf-8'))
    trigger=next(obj for obj in desired.objects if obj.identity.object_type=='TRIGGER')
    proposal=review_source_statement(trigger)
    assert proposal is not None
    assert b'CREATE OR REPLACE TRIGGER APP.TRG' in proposal
    assert b'ALTER TRIGGER' not in proposal


def test_matching_partition_bounds_propose_only_name_changes(tmp_path):
    selected=profile()
    desired=source('CREATE TABLE APP.T(ID NUMBER) PARTITION BY RANGE(ID) INTERVAL(100) '
                   '(PARTITION P1 VALUES LESS THAN(100), PARTITION P2 VALUES LESS THAN(200));')
    target=actual('CREATE TABLE APP.T(ID NUMBER) PARTITION BY RANGE(ID) '
                  '(PARTITION OLD1 VALUES LESS THAN(100), PARTITION OLD2 VALUES LESS THAN(200), '
                  'PARTITION P_MAXVALUE VALUES LESS THAN(MAXVALUE));')
    plan=plan_target(compare_snapshots(desired,target,selected.policy),
                     PlanningContext(desired,target,selected,'Partitions'))
    operation=next(op for op in plan.operations if 'PARTITION_LAYOUT_REQUIRES_REVIEW' in op.reason_codes)
    assert operation.decision=='REVIEW_REQUIRED' and operation.intent is None
    assert operation.proposal is not None
    folder=tmp_path/'bundle'
    write_bundle(plan,folder)
    text=next(folder.glob('proposals/**/op-*.sql')).read_text(encoding='utf-8')
    assert 'RENAME PARTITION "OLD1" TO "P1";' in text
    assert 'RENAME PARTITION "OLD2" TO "P2";' in text
    assert 'SET INTERVAL' not in text and 'DROP PARTITION' not in text


def test_interval_target_proposes_full_range_structure_without_drop(tmp_path):
    selected=profile()
    desired=source('CREATE TABLE APP.T(ID NUMBER) PARTITION BY RANGE(ID) '
                   '(PARTITION SOURCE1 VALUES LESS THAN(100), '
                   'PARTITION SOURCE2 VALUES LESS THAN(200), '
                   'PARTITION SOURCE3 VALUES LESS THAN(300), '
                   'PARTITION P_MAXVALUE VALUES LESS THAN(MAXVALUE));')
    target=actual('CREATE TABLE APP.T(ID NUMBER) PARTITION BY RANGE(ID) INTERVAL(100) '
                  '(PARTITION TARGET1 VALUES LESS THAN(100), '
                  'PARTITION TARGET2 VALUES LESS THAN(200));')
    plan=plan_target(compare_snapshots(desired,target,selected.policy),
                     PlanningContext(desired,target,selected,'Partitions'))
    operation=next(op for op in plan.operations if 'PARTITION_LAYOUT_REQUIRES_REVIEW' in op.reason_codes)
    assert operation.decision=='REVIEW_REQUIRED' and operation.proposal is not None
    folder=tmp_path/'bundle'
    write_bundle(plan,folder)
    sql=next(folder.glob('proposals/**/op-*.sql')).read_text(encoding='utf-8')
    assert 'SET INTERVAL ();' in sql
    assert 'RENAME PARTITION "TARGET1" TO "SOURCE1";' in sql
    assert 'ADD PARTITION "SOURCE3" VALUES LESS THAN (300);' in sql
    assert 'ADD PARTITION "P_MAXVALUE" VALUES LESS THAN (MAXVALUE);' in sql
    assert 'DROP PARTITION' not in sql


def test_character_collation_is_covered_by_ready_numeric_type_change():
    from oracle_db_migration_generator.planning.table_rules import _collation_consumed_by_type
    before={'data_type':KnownValue('KNOWN','VARCHAR2(10)',()),
            'collation':KnownValue('KNOWN','USING_NLS_COMP',())}
    after={'data_type':KnownValue('KNOWN','NUMBER',()),
           'collation':KnownValue('KNOWN',None,())}
    change=SimpleNamespace(decision='READY',kind='MODIFY_COLUMN',
                           reason_codes=('MODIFY_COLUMN_TO_SOURCE',),
                           intent=SimpleNamespace(affected_columns=('SURE',)))
    assert _collation_consumed_by_type(before,after,[change],'SURE')
    assert not _collation_consumed_by_type(before,after,[],'SURE')
    assert not _collation_consumed_by_type(before,after,[change],'OTHER')
