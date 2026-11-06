"""Şema Karşılaştırma önbelleklerinin kanonik çıktıyı ve değişmezliği koruduğunu sınar.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
from dataclasses import replace

from oracle_db_migration_generator.model.serialization import thaw
from oracle_db_migration_generator.model.snapshot import KnownValue
from oracle_db_migration_generator.parsing.canonicalize import (
    canonical_sql, _canonical_sql, _cached_canonical_sql,
)
from tests.factories import source, actual, profile


def test_digest_cache_does_not_enter_serialization_or_survive_replace():
    snapshot = source('CREATE TABLE APP.T(ID NUMBER);')
    before = thaw(snapshot)
    first = snapshot.semantic_digest
    assert snapshot.semantic_digest == first
    assert thaw(snapshot) == before
    changed = replace(snapshot, capabilities={**snapshot.capabilities,
        'test_version': KnownValue('KNOWN', 2, ())})
    assert changed.semantic_digest != first
    assert replace(snapshot).semantic_digest == first


def test_digest_inputs_are_detached_from_mutable_sequence_arguments():
    original = source('CREATE TABLE APP.T(ID NUMBER);')
    schemas, objects = list(original.schemas), list(original.objects)
    diagnostics = list(original.completeness.diagnostics)
    snapshot = replace(original, schemas=schemas, objects=objects,
                       completeness=replace(original.completeness, diagnostics=diagnostics))
    first = snapshot.semantic_digest
    schemas.append('OTHER')
    objects.clear()
    diagnostics.append('CHANGED')
    assert snapshot.semantic_digest == first
    assert replace(snapshot).semantic_digest == first


def test_sql_cache_preserves_literals_quotes_hints_and_skips_large_bodies():
    _cached_canonical_sql.cache_clear()
    samples = ['SELECT "Foo", \'a  B\' FROM dual', 'select /*+ FULL(t) */ x from t',
               'CREATE OR REPLACE VIEW APP.V AS SELECT 1 FROM DUAL;', 'NUMBER(10,2)']
    for text in samples:
        assert canonical_sql(text) == _canonical_sql(text)
        assert canonical_sql(text) == _canonical_sql(text)
    assert _cached_canonical_sql.cache_info().hits == len(samples)
    before = _cached_canonical_sql.cache_info()
    large = 'select ' + ', '.join(str(i) for i in range(1000)) + ' from dual'
    assert canonical_sql(large) == _canonical_sql(large)
    assert _cached_canonical_sql.cache_info() == before


def test_cached_and_uncached_comparison_preserve_plan_and_ddl(monkeypatch):
    from oracle_db_migration_generator.compare.snapshots import compare_snapshots
    from oracle_db_migration_generator.emission.sql import render_statement
    from oracle_db_migration_generator.model.snapshot import SchemaSnapshot
    from oracle_db_migration_generator.parsing import canonicalize
    from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
    selected = profile()
    desired = source('CREATE TABLE APP.T(ID NUMBER, NAME VARCHAR2(20 BYTE)); '
                     'CREATE TABLE APP.NEW_TABLE(ID NUMBER);', selected)
    observed = actual('CREATE TABLE APP.T(ID NUMBER);', selected)
    differences = compare_snapshots(desired, observed, selected.policy)
    fast = plan_target(differences, PlanningContext(desired, observed, selected, 'TEST'))
    getter = SchemaSnapshot.semantic_digest.fget

    def uncached(snapshot):
        object.__setattr__(snapshot, '_semantic_digest_cache', None)
        return getter(snapshot)

    monkeypatch.setattr(SchemaSnapshot, 'semantic_digest', property(uncached))
    monkeypatch.setattr(canonicalize, '_cached_canonical_sql', _canonical_sql)
    slow = plan_target(compare_snapshots(desired, observed, selected.policy),
                       PlanningContext(desired, observed, selected, 'TEST'))
    assert fast.to_dict() == slow.to_dict()
    fast_sql = [render_statement(op, fast.plan_id) for op in fast.operations if op.intent]
    slow_sql = [render_statement(op, slow.plan_id) for op in slow.operations if op.intent]
    assert len(fast_sql) >= 2
    assert fast_sql == slow_sql
