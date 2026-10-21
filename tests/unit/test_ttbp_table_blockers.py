from dataclasses import replace

from oracle_db_migration_generator.compare.projection_adapter import canonical_fields
from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
from tests.factories import actual, profile, source


def test_known_dictionary_columns_survive_an_unavailable_table_projection():
    """A parser failure must not discard independent dictionary column facts."""
    target = actual('CREATE TABLE APP.T(ID NUMBER DEFAULT 1);')
    original = target.objects[0]
    row = {'column_name': 'ID', 'data_type': 'NUMBER', 'data_length': 22,
           'char_length': 0, 'char_used': None, 'data_precision': None,
           'data_scale': None, 'nullable': 'Y', 'data_default': '1',
           'column_id': 1, 'hidden_column': 'NO', 'user_generated': 'YES',
           'identity_column': 'NO', 'virtual_column': 'NO', 'default_on_null': 'NO'}
    obj = replace(original, projection=None,
                  coverage=replace(original.coverage, ddl='PARTIAL', diagnostics=('PARSER_SYNTAX_ERROR',)),
                  properties={**original.properties,
                              'projection': KnownValue('UNKNOWN', None, original.evidence_ids),
                              'definition': KnownValue('UNKNOWN', None, original.evidence_ids),
                              'dictionary.columns': KnownValue('KNOWN', [row], ('ev-target-scope',))})
    target = replace(target, objects=(obj,))

    fields = canonical_fields(obj, target, profile().policy)

    assert fields['/columns/ID/data_type'].state == 'KNOWN'
    assert fields['/columns/ID/data_type'].value == 'NUMBER'
    assert fields['/columns/ID/default'].value == '[["code","1"]]'
    assert fields['/columns/ID/data_type'].evidence_ids == ('ev-target-scope',)
    assert fields['/coverage/ddl'].state == 'UNKNOWN'
    assert fields['/definition'].state == 'UNKNOWN'
    assert not any(path.startswith('/constraints/') or path.startswith('/table_properties/')
                   for path in fields)


def _partial_inventory_plan(desired_sql, target_sql, *, partial_object=False):
    selected = profile()
    desired = source(desired_sql, selected)
    desired = replace(desired, completeness=replace(desired.completeness, inventory='PARTIAL'))
    if partial_object:
        desired = replace(desired, objects=tuple(replace(obj,
            coverage=replace(obj.coverage, ddl='PARTIAL', diagnostics=('PARSER_NOT_VERIFIED',)))
            for obj in desired.objects))
    target = actual(target_sql, selected)
    differences = compare_snapshots(desired, target, selected.policy)
    return plan_target(differences, PlanningContext(desired, target, selected, 'Audit'))


def test_unverified_source_constraint_absence_is_preserved_without_erasing_unknown():
    result = _partial_inventory_plan('CREATE TABLE APP.T(ID NUMBER);',
        'CREATE TABLE APP.T(ID NUMBER, CONSTRAINT CK_T CHECK(ID>0));', partial_object=True)

    assert len(result.operations) == 1
    preserved = result.operations[0]
    assert preserved.decision == 'BLOCKED' and preserved.intent is None
    assert 'OBJECT_METADATA_INCOMPLETE' in preserved.reason_codes
    assert result.scope.inventory == 'PARTIAL'
    assert result.differences and all(diff.kind == 'UNKNOWN' for diff in result.differences)
    assert set(preserved.change_ids) == {diff.difference_id for diff in result.differences}


def test_preserved_constraint_does_not_turn_an_independent_state_change_into_blocked():
    result = _partial_inventory_plan(
        'CREATE TABLE APP.T(ID NUMBER, CONSTRAINT CK_STATE CHECK(ID<100) ENABLE);',
        'CREATE TABLE APP.T(ID NUMBER, CONSTRAINT CK_STATE CHECK(ID<100) DISABLE, '
        'CONSTRAINT CK_PRESERVED CHECK(ID>0));')

    assert len(result.operations) == 2
    assert len({op.operation_id for op in result.operations}) == 2
    assert sorted(op.decision for op in result.operations) == ['INFORMATIONAL', 'REVIEW_REQUIRED']
    assert all(op.intent is None for op in result.operations)
    changed = next(op for op in result.operations if op.decision == 'REVIEW_REQUIRED')
    paths = {diff.property_path for diff in result.differences if diff.difference_id in changed.change_ids}
    assert paths == {'/constraints/CK_STATE/enabled'}
    assert {diff.difference_id for diff in result.differences} == {
        change_id for op in result.operations for change_id in op.change_ids}


def test_unknown_definition_of_a_source_named_constraint_remains_blocked():
    selected = profile()
    desired = source('CREATE TABLE APP.T(ID NUMBER, CONSTRAINT CK_T CHECK(ID>0));')
    obj = desired.objects[0]
    obj = replace(obj, properties={**obj.properties,
        '/constraints/CK_T/condition': KnownValue('UNKNOWN', None, obj.evidence_ids)})
    desired = replace(desired, objects=(obj,))
    target = actual('CREATE TABLE APP.T(ID NUMBER, CONSTRAINT CK_T CHECK(ID>0));')
    result = plan_target(compare_snapshots(desired, target, selected.policy),
                         PlanningContext(desired, target, selected, 'Audit'))

    assert len(result.operations) == 1
    assert result.operations[0].decision == 'BLOCKED'
    assert result.operations[0].intent is None


def test_supplemental_logging_obeys_the_physical_storage_comparison_policy():
    target = actual('CREATE TABLE APP.T(ID NUMBER);')
    obj = target.objects[0]
    projection = replace(obj.projection, properties={**obj.projection.properties,
        'table_properties': {**obj.projection.properties['table_properties'],
                             'supplemental_logging': 'SUPPLEMENTAL LOG GROUP G_T (ID) ALWAYS'}})
    obj = replace(obj, projection=projection)

    ignored = canonical_fields(obj, target, profile().policy)
    compared = canonical_fields(obj, target, replace(profile().policy, compare_physical_storage=True))

    assert '/table_properties/supplemental_logging' not in ignored
    assert compared['/table_properties/supplemental_logging'].state == 'KNOWN'
    assert compared['/table_properties/supplemental_logging'].value == (
        '[["code","SUPPLEMENTAL"],["code","LOG"],["code","GROUP"],'
        '["code","G_T"],["code","("],["code","ID"],["code",")"],["code","ALWAYS"]]')


def _column_plan(desired_sql, target_sql):
    selected = profile()
    desired = source(desired_sql, selected)
    target = actual(target_sql, selected)
    return plan_target(compare_snapshots(desired, target, selected.policy),
                         PlanningContext(desired, target, selected, 'Audit'))


def test_unknown_only_existing_column_is_preserved_without_claiming_a_complete_comparison():
    result = _column_plan('CREATE TABLE APP.T(C VARCHAR2(20 BYTE));',
        'CREATE TABLE APP.T(C VARCHAR2(20 BYTE) COLLATE USING_NLS_COMP);')

    assert len(result.operations) == 1
    op = result.operations[0]
    assert op.decision == 'INFORMATIONAL' and op.intent is None
    assert 'COLUMN_COMPARISON_INCOMPLETE_PRESERVED' in op.reason_codes
    assert len(result.differences) == 1 and result.differences[0].kind == 'UNKNOWN'
    assert result.differences[0].after.state == 'UNKNOWN'
    assert result.status == 'BLOCKED'


def test_unknown_collation_with_a_known_width_change_still_blocks_the_column():
    result = _column_plan('CREATE TABLE APP.T(C VARCHAR2(30 BYTE));',
        'CREATE TABLE APP.T(C VARCHAR2(20 BYTE) COLLATE USING_NLS_COMP);')

    op = next(op for op in result.operations if 'COLUMN_METADATA_UNKNOWN' in op.reason_codes)
    assert op.decision == 'BLOCKED' and op.intent is None
    assert any(diff.property_path.endswith('/length') and diff.kind == 'CHANGED'
               for diff in result.differences)


def test_unknown_semantics_of_a_missing_column_are_not_a_preservation_warning():
    selected = replace(profile(), source_length_semantics='UNKNOWN')
    desired = source('CREATE TABLE APP.T(ID NUMBER, C VARCHAR2(20));', selected)
    target = actual('CREATE TABLE APP.T(ID NUMBER);', selected)
    result = plan_target(compare_snapshots(desired, target, selected.policy),
                         PlanningContext(desired, target, selected, 'Audit'))

    assert any('COLUMN_METADATA_UNKNOWN' in op.reason_codes and op.decision == 'BLOCKED'
               for op in result.operations)
    assert not any('COLUMN_COMPARISON_INCOMPLETE_PRESERVED' in op.reason_codes
                   for op in result.operations)


def test_partial_target_ddl_cannot_use_the_unknown_only_column_preservation_guard():
    selected = profile()
    desired = source('CREATE TABLE APP.T(C VARCHAR2(20 BYTE));', selected)
    target = actual('CREATE TABLE APP.T(C VARCHAR2(20 BYTE) COLLATE USING_NLS_COMP);', selected)
    obj = target.objects[0]
    obj = replace(obj, coverage=replace(obj.coverage, ddl='PARTIAL', diagnostics=('PARSER_SYNTAX_ERROR',)))
    target = replace(target, objects=(obj,))
    result = plan_target(compare_snapshots(desired, target, selected.policy),
                         PlanningContext(desired, target, selected, 'Audit'))

    assert any('COLUMN_METADATA_UNKNOWN' in op.reason_codes and op.decision == 'BLOCKED'
               for op in result.operations)
    assert not any('COLUMN_COMPARISON_INCOMPLETE_PRESERVED' in op.reason_codes
                   for op in result.operations)


def test_nullability_change_is_reviewed_independently_of_unknown_collation():
    result = _column_plan('CREATE TABLE APP.T(C VARCHAR2(20 BYTE) NOT NULL);',
        'CREATE TABLE APP.T(C VARCHAR2(20 BYTE) COLLATE USING_NLS_COMP);')

    assert sorted(op.decision for op in result.operations) == ['INFORMATIONAL', 'REVIEW_REQUIRED']
    review = next(op for op in result.operations if op.decision == 'REVIEW_REQUIRED')
    assert review.intent is None
    assert {diff.property_path for diff in result.differences if diff.difference_id in review.change_ids} == {
        '/columns/C/nullable'}
    assert any(diff.kind == 'UNKNOWN' for diff in result.differences)
    assert result.status == 'BLOCKED'


def test_default_removal_and_nullability_review_do_not_require_unknown_character_settings():
    selected = replace(profile(), source_length_semantics='UNKNOWN')
    desired = source('CREATE TABLE APP.T(C VARCHAR2(20));', selected)
    target = actual("CREATE TABLE APP.T(C VARCHAR2(20 BYTE) COLLATE USING_NLS_COMP DEFAULT 'COUNT(*)' NOT NULL);", selected)
    result = plan_target(compare_snapshots(desired, target, selected.policy),
                         PlanningContext(desired, target, selected, 'Audit'))

    assert sorted(op.decision for op in result.operations) == ['INFORMATIONAL', 'READY', 'REVIEW_REQUIRED']
    default = next(op for op in result.operations if op.decision == 'READY')
    assert default.intent.statement == b'ALTER TABLE "APP"."T" MODIFY ("C" DEFAULT NULL);'
    assert all(op.intent is None for op in result.operations if op is not default)
    assert sum(diff.kind == 'UNKNOWN' for diff in result.differences) == 2
    assert result.status == 'BLOCKED'


def test_a_known_width_change_keeps_default_and_unknown_collation_together_blocked():
    result = _column_plan('CREATE TABLE APP.T(C VARCHAR2(30 BYTE) DEFAULT 2);',
        'CREATE TABLE APP.T(C VARCHAR2(20 BYTE) COLLATE USING_NLS_COMP DEFAULT 1);')

    assert len(result.operations) == 1
    assert result.operations[0].decision == 'BLOCKED'
    assert result.operations[0].intent is None
    assert 'COLUMN_METADATA_UNKNOWN' in result.operations[0].reason_codes


def test_preserved_unknown_parent_column_does_not_release_a_foreign_key():
    selected = profile()
    desired = source('CREATE TABLE APP.P(C VARCHAR2(20 BYTE), CONSTRAINT PK_P PRIMARY KEY(C)); '
        'CREATE TABLE APP.CHILD(C VARCHAR2(20 BYTE) COLLATE USING_NLS_COMP, '
        'CONSTRAINT FK_CHILD FOREIGN KEY(C) REFERENCES APP.P(C));', selected)
    target = actual('CREATE TABLE APP.P(C VARCHAR2(20 BYTE) COLLATE USING_NLS_COMP, '
                    'CONSTRAINT PK_P PRIMARY KEY(C));', selected)
    target = replace(target, capabilities={**target.capabilities,
        'data_bound_collation_enabled': KnownValue('KNOWN', True, ('ev-target-scope',))})
    result = plan_target(compare_snapshots(desired, target, selected.policy),
                         PlanningContext(desired, target, selected, 'Audit'))

    assert any('COLUMN_COMPARISON_INCOMPLETE_PRESERVED' in op.reason_codes
               and op.decision == 'INFORMATIONAL' for op in result.operations)
    fk = next(op for op in result.operations if op.kind == 'ADD_CONSTRAINT')
    assert fk.decision == 'BLOCKED' and fk.intent is None
