"""Preservation must not require proving unknown source membership absent."""
from dataclasses import replace

import pytest

from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
from oracle_db_migration_generator.parsing.dependencies import references
from tests.factories import actual, profile, source


def plan(desired, target):
    selected = profile()
    differences = compare_snapshots(desired, target, selected.policy)
    return differences, plan_target(differences, PlanningContext(desired, target, selected, 'Preservation'))


@pytest.mark.parametrize('target_sql', [
    'CREATE TABLE APP.EXTRA_OBJECT(ID NUMBER);',
    'CREATE INDEX APP.EXTRA_OBJECT ON APP.P(ID);',
    'CREATE PROCEDURE APP.EXTRA_OBJECT AS BEGIN NULL; END;\n/',
])
def test_unknown_source_membership_preserves_observed_target_without_claiming_absence(target_sql):
    desired = source('CREATE TABLE APP.P(ID NUMBER);')
    desired = replace(desired, completeness=replace(desired.completeness, inventory='PARTIAL',
                                                  diagnostics=('SOURCE_FILE_UNPARSED',)))
    target = actual(target_sql)
    original = target.to_dict()
    differences, result = plan(desired, target)
    diff = next(item for item in differences.differences if item.before.state == 'KNOWN')
    operation = next(item for item in result.operations if item.identity.name.effective_name == 'EXTRA_OBJECT')
    assert diff.kind == 'UNKNOWN' and diff.after.state == 'UNKNOWN'
    assert operation.kind == 'PRESERVE' and operation.decision == 'INFORMATIONAL'
    assert operation.intent is None and operation.sql is None
    assert 'TARGET_OBJECT_PRESERVED_SOURCE_PRESENCE_UNKNOWN' in operation.reason_codes
    assert any('TARGET_OBJECT_PRESERVED_SOURCE_PRESENCE_UNKNOWN' in warning for warning in result.warnings)
    assert result.status == 'BLOCKED' and not differences.complete
    assert differences.scope.inventory == 'PARTIAL'
    assert 'SOURCE_INVENTORY_PARTIAL' in result.warnings
    assert target.to_dict() == original


def test_unknown_target_absence_still_blocks_creating_source_object():
    desired = source('CREATE TABLE APP.P(ID NUMBER);')
    target = actual()
    target = replace(target, completeness=replace(target.completeness, inventory='PARTIAL'))
    differences, result = plan(desired, target)
    assert differences.differences[0].before.state == 'UNKNOWN'
    assert result.operations[0].decision == 'BLOCKED'
    assert result.operations[0].intent is None


def test_required_shared_definition_remains_blocked_when_target_parse_is_unknown():
    sql = 'CREATE PROCEDURE APP.P AS BEGIN NULL; END;\n/'
    desired, target = source(sql), actual(sql)
    obj = target.objects[0]
    target = replace(target, objects=(replace(obj, projection=None,
        properties={**obj.properties, 'projection': KnownValue('UNKNOWN', None, obj.evidence_ids),
                    'definition': KnownValue('UNKNOWN', None, obj.evidence_ids)},
        coverage=replace(obj.coverage, ddl='PARTIAL', diagnostics=('PARSER_SYNTAX_ERROR',))),),
        completeness=replace(target.completeness, ddl='PARTIAL'))
    differences, result = plan(desired, target)
    assert any(diff.kind == 'UNKNOWN' for diff in differences.differences)
    assert result.operations[0].decision == 'BLOCKED' and result.operations[0].intent is None


def declared_object(sql, dependencies):
    obj = source(sql).objects[0]
    return replace(obj, properties={**obj.properties,
        'dependencies': KnownValue('KNOWN', dependencies, obj.evidence_ids)})


@pytest.mark.parametrize('datatype,declared,wanted', [
    ('T.ID%TYPE', [{'owner': 'APP', 'name': 'T', 'type': 'TABLE'}],
     ('APP', 'TABLE', 'T', 'ANCHORED_COLUMN_TYPE', ('ID',))),
    ('APP.T.ID%TYPE', [], ('APP', 'TABLE', 'T', 'ANCHORED_COLUMN_TYPE', ('ID',))),
    ('T%ROWTYPE', [{'owner': 'APP', 'name': 'T', 'type': 'TABLE'}],
     ('APP', 'TABLE', 'T', 'ANCHORED_ROWTYPE', ())),
    ('OTHER.T%ROWTYPE', [], ('OTHER', 'TABLE', 'T', 'ANCHORED_ROWTYPE', ())),
])
def test_anchored_routine_types_reference_real_parent_and_columns(datatype, declared, wanted):
    obj = declared_object(f'CREATE PROCEDURE APP.P(ARG {datatype}) AS BEGIN NULL; END;\n/', declared)
    refs = references(obj)
    assert wanted in {(ref.owner, ref.object_type, ref.name, ref.role, ref.columns) for ref in refs}
    assert not any(ref.object_type == 'TYPE_SPEC' for ref in refs)


def test_unproven_record_field_anchor_does_not_invent_cross_schema_type():
    obj = declared_object('CREATE PROCEDURE APP.P(ARG REC.FIELD%TYPE) AS BEGIN NULL; END;\n/', [])
    refs = references(obj)
    assert not any(ref.owner == 'REC' for ref in refs)
    assert any(ref.role == 'ANCHORED_REFERENCE_UNRESOLVED' for ref in refs)


def test_proven_package_member_call_uses_own_schema_package_dependency():
    obj = declared_object('CREATE PROCEDURE APP.P AS BEGIN PKG.DO_WORK; END;\n/',
                          [{'owner': 'APP', 'name': 'PKG', 'type': 'PACKAGE'}])
    refs = references(obj)
    assert any(ref.owner == 'APP' and ref.object_type == 'PACKAGE_SPEC' and ref.name == 'PKG'
               and ref.role == 'ROUTINE_CALL' for ref in refs)
    assert not any(ref.owner == 'PKG' and ref.name == 'DO_WORK' for ref in refs)


def test_unproven_two_part_call_does_not_assume_own_schema_package():
    obj = declared_object('CREATE PROCEDURE APP.P AS BEGIN OTHER.DO_WORK; END;\n/', [])
    assert any(ref.owner == 'OTHER' and ref.object_type == 'CALLABLE' and ref.name == 'DO_WORK'
               for ref in references(obj))


@pytest.mark.parametrize('target_sql,expected', [
    ('CREATE TABLE APP.T(ID NUMBER);', 'READY'),
    ('CREATE TABLE APP.T(OTHER_ID NUMBER);', 'BLOCKED'),
    ('CREATE PACKAGE APP.T AS ID NUMBER; END;\n/', 'BLOCKED'),
])
def test_anchored_parameter_requires_actual_table_and_named_column(target_sql, expected):
    sql = 'CREATE PROCEDURE APP.P(ARG T.ID%TYPE) AS BEGIN NULL; END;\n/'
    desired = source(sql)
    obj = desired.objects[0]
    desired = replace(desired, objects=(replace(obj, properties={**obj.properties,
        'dependencies': KnownValue('KNOWN', [{'owner': 'APP', 'type': 'TABLE', 'name': 'T'}], obj.evidence_ids)}),))
    _, result = plan(desired, actual(target_sql))
    routine = next(op for op in result.operations if op.identity.name.effective_name == 'P')
    assert routine.decision == expected
    assert (routine.intent is not None) == (expected == 'READY')


def test_multiple_anchored_columns_have_deterministic_reference_order():
    obj = declared_object('CREATE PROCEDURE APP.P(P_Z T.Z%TYPE, P_B T.B%TYPE, P_A T.A%TYPE, '
                          'P_D T.D%TYPE, P_C T.C%TYPE) AS BEGIN NULL; END;\n/',
                          [{'owner': 'APP', 'name': 'T', 'type': 'TABLE'}])
    columns = [ref.columns for ref in references(obj) if ref.role == 'ANCHORED_COLUMN_TYPE']
    assert columns == [('A',), ('B',), ('C',), ('D',), ('Z',)]


def test_unresolved_anchor_graph_reports_unknown_binding_without_claiming_target_absence():
    desired = source('CREATE PROCEDURE APP.P(ARG REC.FIELD%TYPE) AS BEGIN NULL; END;\n/')
    obj = desired.objects[0]
    desired = replace(desired, objects=(replace(obj, properties={**obj.properties,
        'dependencies': KnownValue('KNOWN', [], obj.evidence_ids)}),))
    _, result = plan(desired, actual())
    routine = next(op for op in result.operations if op.identity.name.effective_name == 'P')
    assert routine.decision == 'BLOCKED' and routine.intent is None
    assert '%TYPE/%ROWTYPE' in routine.reason_tr and 'bağlamı' in routine.reason_tr
    assert 'doğrulanamadı' in routine.reason_tr
    assert 'hedefte bulunamadı' not in routine.reason_tr
    assert 'hedefteki görünürlüğü' not in routine.reason_tr


def test_collection_table_expression_does_not_invent_a_table_named_table():
    obj = source('CREATE VIEW APP.V AS SELECT COLUMN_VALUE FROM TABLE(SYS.ODCINUMBERLIST(1));').objects[0]
    assert not any(ref.name == 'TABLE' and ref.object_type == 'RELATION' for ref in references(obj))


def test_quoted_table_keyword_stays_a_real_relation():
    obj = source('CREATE VIEW APP.V AS SELECT ID FROM "TABLE";').objects[0]
    assert any(ref.owner == 'APP' and ref.name == 'TABLE' and ref.object_type == 'RELATION'
               for ref in references(obj))


def test_analyzer_proven_package_local_names_use_oracle_identifier_case():
    sql = ('CREATE PACKAGE BODY APP.PKG AS '
           'PROCEDURE local_work IS BEGIN NULL; END; '
           'PROCEDURE caller IS BEGIN local_work; external_work; END; END;\n/')
    obj = source(sql).objects[0]
    assert obj.coverage.ddl == 'COMPLETE'
    refs = references(obj)
    assert not any(ref.name == 'LOCAL_WORK' and ref.role == 'ROUTINE_CALL' for ref in refs)
    assert any(ref.name == 'EXTERNAL_WORK' and ref.role == 'ROUTINE_CALL' for ref in refs)


def test_same_name_call_outside_package_keeps_its_external_reference():
    package = source('CREATE PACKAGE BODY APP.PKG AS PROCEDURE local_work IS BEGIN NULL; END; END;\n/').objects[0]
    external = source('CREATE PROCEDURE APP.P AS BEGIN local_work; END;\n/').objects[0]
    assert not any(ref.name == 'LOCAL_WORK' for ref in references(package))
    assert any(ref.owner == 'APP' and ref.name == 'LOCAL_WORK' and ref.role == 'ROUTINE_CALL'
               for ref in references(external))


def test_quoted_local_name_does_not_hide_different_case_external_call():
    obj = source('CREATE PACKAGE BODY APP.PKG AS PROCEDURE "lower" IS BEGIN NULL; END; '
                 'PROCEDURE caller IS BEGIN "lower"; "LOWER"; END; END;\n/').objects[0]
    refs = references(obj)
    assert not any(ref.name == 'lower' and ref.role == 'ROUTINE_CALL' for ref in refs)
    assert any(ref.name == 'LOWER' and ref.role == 'ROUTINE_CALL' for ref in refs)
