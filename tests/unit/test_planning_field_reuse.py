"""Şema Karşılaştırma aynı plan içindeki kolon hesaplarını ve hedef ayrımını sınar.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
from dataclasses import replace

from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.planning.context import PlanningContext
from oracle_db_migration_generator.planning.rules import plan_target
from oracle_db_migration_generator.planning import table_rules
from oracle_db_migration_generator.model.snapshot import KnownValue
from tests.factories import actual, profile, source


def test_many_indexes_reuse_table_fields_with_identical_sql_and_decisions(monkeypatch):
    selected = profile()
    table = 'CREATE TABLE APP.T(ID NUMBER, CODE VARCHAR2(10 BYTE));'
    indexes = [f'CREATE INDEX APP.IX{i} ON APP.T(CODE);' for i in range(12)]
    desired = source(table + ''.join(indexes), selected)
    observed = actual(table, selected)
    changes = compare_snapshots(desired, observed, selected.policy)
    reads = []
    original = table_rules.table_columns
    def counted(obj, snapshot):
        reads.append((snapshot.side, obj.object_key))
        return original(obj, snapshot)
    monkeypatch.setattr(table_rules, 'table_columns', counted)
    plan = plan_target(changes, PlanningContext(desired, observed, selected, 'Test'))
    operations = [op for op in plan.operations if op.identity.object_type == 'INDEX']
    assert len(operations) == 12
    assert all(op.decision == 'READY' and op.intent for op in operations)
    assert {op.intent.statement for op in operations} == {sql.encode() for sql in indexes}
    assert all(op.dependencies == () for op in operations)
    assert len(reads) <= 2, f'Aynı tablonun kolonları {len(reads)} kez hesaplandı'


def test_field_cache_is_bound_to_target_context_and_preserves_unknowns():
    selected = profile()
    desired = source('CREATE TABLE APP.T(CODE VARCHAR2(20 BYTE));', selected)
    short = actual('CREATE TABLE APP.T(CODE VARCHAR2(10 BYTE));', selected)
    long = replace(actual('CREATE TABLE APP.T(CODE VARCHAR2(40 BYTE));', selected), target_id='SECOND')
    first = PlanningContext(desired, short, selected, 'First')
    second = PlanningContext(desired, long, selected, 'Second')
    table = desired.objects[0]
    assert first.column_fields(table)['CODE']['length'].value == 20
    assert first.column_fields(short.objects[0], desired=False)['CODE']['length'].value == 10
    assert second.column_fields(long.objects[0], desired=False)['CODE']['length'].value == 40
    assert first.column_fields(short.objects[0], desired=False)['CODE']['length'].value == 10
    incomplete = replace(short.objects[0], projection=None, properties={
        'CODE.length': KnownValue('UNKNOWN', None, short.objects[0].evidence_ids)})
    assert first.column_fields(incomplete, desired=False)['CODE']['length'].state == 'UNKNOWN'
