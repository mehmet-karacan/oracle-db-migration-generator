"""Şema Karşılaştırma birim kararlarında aynı SQL metninin tekrar okunmasını sınar.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.planning.context import PlanningContext
from oracle_db_migration_generator.planning import object_rules
from tests.factories import actual, profile, source


def test_package_decision_reuses_tokens_and_preserves_source_body(monkeypatch):
    selected = profile()
    raw = 'CREATE PACKAGE APP.P AS /* açıklama */ PROCEDURE R; END P;'
    desired = source(raw, selected)
    observed = actual('', selected)
    changes = compare_snapshots(desired, observed, selected.policy)
    obj = desired.objects[0]
    calls = []
    tokenize = object_rules.code_tokens
    def counted(text):
        calls.append(text)
        return tokenize(text)
    monkeypatch.setattr(object_rules, 'code_tokens', counted)
    operations = object_rules.object_change(PlanningContext(desired, observed, selected, 'Test'),
                                            obj, None, changes.differences)
    assert len(operations) == 1
    op = operations[0]
    assert op.decision == 'READY' and op.kind == 'CREATE'
    assert op.intent.statement == 'CREATE OR REPLACE PACKAGE APP.P AS /* açıklama */ PROCEDURE R; END P;'.encode()
    assert calls == [raw]
