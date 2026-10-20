"""Supplemental logging clauses are table metadata, never fabricated columns."""
from dataclasses import replace

from oracle_db_migration_generator.parsing.adapter import parse_ddl
from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.planning.rules import PlanningContext,plan_target
from tests.factories import source,actual,profile


def logging_table():
    return ('CREATE TABLE APP.T (ID NUMBER, NOTE NUMBER, '
            'SUPPLEMENTAL LOG GROUP LG_ONE (ID) ALWAYS, '
            'SUPPLEMENTAL LOG GROUP LG_TWO (ID, NOTE), '
            'SUPPLEMENTAL LOG DATA (ALL) COLUMNS);')


def test_valid_logging_groups_never_become_columns_or_duplicate_column_errors():
    raw=logging_table().encode()
    result=parse_ddl(raw,None)
    assert result.coverage=='COMPLETE' and not result.diagnostics
    obj=result.objects[0]
    assert obj.parse_ok and not obj.diagnostics and obj.raw_ddl==raw
    assert set(obj.projection.properties['columns'])=={'ID','NOTE'}
    assert len(obj.projection.properties['_generator_supplemental_logging'])==3


def test_new_table_retains_all_verified_logging_clauses_without_fake_type_dependencies():
    selected=profile();desired=source(logging_table());target=actual()
    result=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Audit'))
    create=next(op for op in result.operations if op.kind=='CREATE')
    assert create.decision=='READY'
    statement=create.intent.statement
    assert statement.count(b'SUPPLEMENTAL LOG GROUP')==2
    assert b'SUPPLEMENTAL LOG DATA (ALL) COLUMNS' in statement
    assert not any(ref.name=='LOG' for ref in create.intent.references)
    assert parse_ddl(statement,None).coverage=='COMPLETE'


def test_existing_target_logging_is_reported_as_warning_and_no_alter_is_emitted():
    selected=profile();desired=source('CREATE TABLE APP.T(ID NUMBER, NOTE NUMBER);');target=actual(logging_table())
    result=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Audit'))
    assert not result.operations
    assert any('TARGET_SUPPLEMENTAL_LOGGING_PRESERVED' in warning and 'APP.T' in warning for warning in result.warnings)


def test_quoted_business_column_named_supplemental_is_preserved():
    result=parse_ddl(b'CREATE TABLE APP.T("SUPPLEMENTAL" NUMBER, ID NUMBER);',None)
    assert result.coverage=='COMPLETE'
    assert set(result.objects[0].projection.properties['columns'])=={'SUPPLEMENTAL','ID'}


def test_logging_group_cannot_reference_an_unknown_column():
    result=parse_ddl(b'CREATE TABLE APP.T(ID NUMBER, SUPPLEMENTAL LOG GROUP LG_BAD (MISSING_ID) ALWAYS);',None)
    assert result.coverage=='PARTIAL'
    assert 'SUPPLEMENTAL_LOG_COLUMN_UNVERIFIED' in result.objects[0].diagnostics


def test_explicit_physical_comparison_does_not_generate_logging_change_sql():
    selected=replace(profile(),policy=replace(profile().policy,compare_physical_storage=True))
    desired=source(logging_table().replace('LG_ONE','LG_CHANGED'),selected);target=actual(logging_table(),selected)
    result=plan_target(compare_snapshots(desired,target,selected.policy),PlanningContext(desired,target,selected,'Audit'))
    assert any(op.decision in {'BLOCKED','REVIEW_REQUIRED'} for op in result.operations)
    assert not any(op.intent for op in result.operations)
