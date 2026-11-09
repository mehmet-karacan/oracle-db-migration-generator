"""Şema Karşılaştırma paket özetlerini gerçek parser çıktısıyla doğrular.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
from dataclasses import replace
import hashlib

import pytest

from oracle_db_migration_generator.model.identity import Identifier, ObjectIdentity
from oracle_db_migration_generator.model.snapshot import Coverage, KnownValue, SnapshotObject
from oracle_db_migration_generator.model.serialization import thaw
from oracle_db_migration_generator.oracle import ddl_model
from oracle_db_migration_generator.parsing.adapter import parse_ddl
from oracle_db_migration_generator.parsing.canonicalize import canonical_sql


SQL = b'CREATE OR REPLACE PACKAGE BODY APP.P AS PROCEDURE R IS BEGIN NULL; END; END P;'


def object_for(raw, kind='PACKAGE_BODY'):
    identity = ObjectIdentity('demo-source', Identifier.parse('APP'), kind, Identifier.parse('P'))
    return SnapshotObject(identity, {}, 'p.sql', hashlib.sha256(raw).hexdigest(),
                          Coverage('COMPLETE', 'COMPLETE', 'COMPLETE'), ('target-evidence',), raw)


def verified_source(raw=SQL, kind='PACKAGE_BODY'):
    obj = object_for(raw, kind)
    parsed = parse_ddl(raw, obj.identity)
    assert parsed.coverage == 'COMPLETE'
    candidate = parsed.objects[0]
    return replace(obj, projection=candidate.projection, properties={
        'projection': KnownValue('KNOWN', thaw(candidate.projection.properties), ('source-evidence',)),
        'definition': KnownValue('KNOWN', canonical_sql(candidate.raw_ddl.decode()), ('source-evidence',))})


@pytest.mark.parametrize('kind,raw', [('PACKAGE_BODY', SQL),
    ('PACKAGE_SPEC', b'CREATE OR REPLACE PACKAGE APP.P AS PROCEDURE R; END P;')])
def test_exact_sha_reuses_verified_package_without_parser(monkeypatch, kind, raw):
    source = verified_source(raw, kind)
    target = object_for(raw, kind)
    baseline = ddl_model.project_target_object(target)
    monkeypatch.setattr(ddl_model, 'parse_ddl', lambda *a, **k: pytest.fail('identical package was parsed'))
    actual = ddl_model.project_target_object(target, source=source)
    assert actual[0].to_dict() == baseline[0].to_dict()
    assert actual[1] == baseline[1]
    assert actual[0].raw_ddl == raw


def test_formatting_only_package_reuses_but_keeps_target_bytes(monkeypatch):
    source = verified_source()
    raw = SQL.replace(b' AS ', b"\r\n AS /* user's ordinary comment */\n ").replace(b' BEGIN ', b'\n BEGIN ')
    target = object_for(raw)
    baseline = ddl_model.project_target_object(target)
    monkeypatch.setattr(ddl_model, 'parse_ddl', lambda *a, **k: pytest.fail('equivalent package was parsed'))
    actual, evidence = ddl_model.project_target_object(target, source=source)
    assert actual.properties['definition'] == baseline[0].properties['definition']
    assert actual.raw_ddl == raw and actual.ddl_sha256 == target.ddl_sha256
    assert actual.coverage == baseline[0].coverage and evidence == ()


@pytest.mark.parametrize('raw', [SQL.replace(b'NULL', b'COMMIT'),
    SQL.replace(b'NULL;', b"DBMS_OUTPUT.PUT_LINE('Mixed Case');"),
    SQL.replace(b'BEGIN NULL', b'BEGIN /*+ important */ NULL'),
    SQL.replace(b'APP.P', b'APP.Q'), SQL + b' @', SQL + b' DROP TABLE APP.T;'])
def test_changed_or_invalid_package_uses_full_parser(monkeypatch, raw):
    source = verified_source()
    calls = []
    real = ddl_model.parse_ddl
    def tracked(*a, **k):
        calls.append(a[0])
        return real(*a, **k)
    monkeypatch.setattr(ddl_model, 'parse_ddl', tracked)
    ddl_model.project_target_object(object_for(raw), source=source)
    assert calls == [raw]


@pytest.mark.parametrize('change', ['partial', 'hash', 'projection', 'identity'])
def test_unverified_source_never_skips_target_parser(monkeypatch, change):
    source = verified_source()
    if change == 'partial': source = replace(source, coverage=replace(source.coverage, ddl='PARTIAL'))
    if change == 'hash': source = replace(source, ddl_sha256='0'*64)
    if change == 'projection': source = replace(source, projection=None, properties={})
    if change == 'identity': source = replace(source, identity=replace(source.identity, name=Identifier.parse('Q')))
    calls = []
    real = ddl_model.parse_ddl
    def tracked(*a, **k):
        calls.append(a[0])
        return real(*a, **k)
    monkeypatch.setattr(ddl_model, 'parse_ddl', tracked)
    ddl_model.project_target_object(object_for(SQL), source=source)
    assert calls == [SQL]


def test_changed_and_unchanged_packages_keep_generated_sql(tmp_path):
    from tests.factories import source, actual, profile
    from oracle_db_migration_generator.runtime.worker import offline_plan
    selected = profile()
    spec = 'CREATE PACKAGE APP.P AS PROCEDURE R; END P;\n/\n'
    before = SQL.decode() + '\n/\n'
    after = before.replace('NULL;', 'NULL; NULL;')
    desired = source(spec + after, selected)
    observed = actual(spec + before, selected)
    by_key = {obj.object_key: obj for obj in desired.objects}
    baseline_objects, fast_objects = [], []
    for obj in observed.objects:
        baseline_objects.append(ddl_model.project_target_object(obj)[0])
        fast_objects.append(ddl_model.project_target_object(obj, source=by_key[obj.object_key])[0])
    offline_plan(desired, replace(observed, objects=tuple(baseline_objects)), selected, tmp_path/'baseline')
    offline_plan(desired, replace(observed, objects=tuple(fast_objects)), selected, tmp_path/'fast')
    sql_files = lambda root: {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*.sql')}
    baseline = sql_files(tmp_path/'baseline')
    assert baseline and any(b'NULL; NULL;' in raw for raw in baseline.values())
    assert sql_files(tmp_path/'fast') == baseline


def test_live_collector_checks_sha_before_package_parser(monkeypatch):
    from tests.factories import source
    from tests.unit.test_collector import FakeConnection, FakeCursor, inputs
    from oracle_db_migration_generator.config.credentials import Credentials
    from oracle_db_migration_generator.oracle.collector import collect_target
    raw = b'CREATE PACKAGE APP.P AS PROCEDURE R; END P;'
    desired = source(raw.decode())
    class Cursor(FakeCursor):
        """Paket toplama testinde sabit envanter ve DDL döndürür.

        Author: Mehmet KARACAN
        Date: 2026-11-06
        """
        def __init__(self):
            super().__init__(inventory=[('PACKAGE', 'P', 'VALID', '2026-11-06')])
        def fetchone(self):
            if 'GET_DDL' in self.current.upper(): return (raw.decode(),)
            return super().fetchone()
    connection = FakeConnection()
    connection.reader = Cursor()
    monkeypatch.setattr(ddl_model, 'parse_ddl', lambda *a, **k: pytest.fail('collector parsed identical package'))
    target, profile = inputs()
    result = collect_target(target, lambda _: Credentials('APP', 'synthetic'), profile,
                            connect=lambda *_: connection, source=desired)
    assert result.snapshot is not None
    assert result.snapshot.objects[0].properties['definition'].state == 'KNOWN'
    assert result.receipt['schemas'][0]['package_sha_reuse'] == {'raw_sha_match': 1, 'content_sha_match': 0}
    assert connection.closed


def test_slash_inside_literal_is_not_a_runner_separator(monkeypatch):
    desired = SQL.replace(b'NULL;', b"DBMS_OUTPUT.PUT_LINE('first\n/\nlast');")
    source = verified_source(desired)
    raw = desired.replace(b'first\n/\nlast', b'first\nlast')
    calls = []
    real = ddl_model.parse_ddl
    def tracked(*a, **k):
        calls.append(a[0])
        return real(*a, **k)
    monkeypatch.setattr(ddl_model, 'parse_ddl', tracked)
    ddl_model.project_target_object(object_for(raw), source=source)
    assert calls == [raw]


def test_verified_source_package_review_does_not_parse_again(monkeypatch):
    from oracle_db_migration_generator.planning.object_rules import review_source_statement
    source = verified_source()
    monkeypatch.setattr('oracle_db_migration_generator.parsing.adapter.parse_ddl',
                        lambda *a, **k: pytest.fail('verified source package parsed again'))
    assert review_source_statement(source) == SQL


def test_verified_package_emission_keeps_identical_bytes(monkeypatch):
    from tests.factories import source, actual, profile
    from oracle_db_migration_generator.compare.snapshots import compare_snapshots
    from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
    from oracle_db_migration_generator.emission import sql
    selected = profile()
    spec = 'CREATE PACKAGE APP.P AS PROCEDURE R; END P;\n/\n'
    before = SQL.decode() + '\n/\n'
    desired = source(spec + before.replace('NULL;', 'NULL; NULL;'), selected)
    observed = actual(spec + before, selected)
    plan = plan_target(compare_snapshots(desired, observed, selected.policy),
                       PlanningContext(desired, observed, selected, 'Test'))
    op = next(op for op in plan.operations if op.intent)
    original = next(obj for obj in desired.objects if obj.object_key == op.identity.key)
    baseline = sql.render_statement(op, plan.plan_id)
    real = sql.parse_ddl
    calls = []
    def tracked(*a, **k):
        calls.append(a[0])
        return real(*a, **k)
    monkeypatch.setattr(sql, 'parse_ddl', tracked)
    assert sql.render_statement(op, plan.plan_id, source=original) == baseline
    assert calls == []
    # Farklı bir gövde için aynı kaynak kanıtı kullanılamaz.
    changed = op.intent.statement.replace(b'NULL; NULL;', b'NULL;')
    altered = replace(op, intent=replace(op.intent, statement=changed,
                                       verification_sha256=hashlib.sha256(changed).hexdigest()))
    sql.render_statement(altered, plan.plan_id, source=original)
    assert calls == [changed]


@pytest.mark.parametrize('kind,raw', [
    ('PROCEDURE', b'CREATE PROCEDURE APP.P IS BEGIN NULL; END;'),
    ('FUNCTION', b'CREATE FUNCTION APP.P RETURN NUMBER IS BEGIN RETURN 1; END;'),
    ('VIEW', b'CREATE VIEW APP.P AS SELECT 1 AS ID FROM DUAL;')])
def test_verified_replacement_source_review_reuses_exact_definition(monkeypatch, kind, raw):
    from oracle_db_migration_generator.planning.object_rules import review_source_statement
    obj = verified_source(raw, kind)
    monkeypatch.setattr('oracle_db_migration_generator.parsing.adapter.parse_ddl',
                        lambda *a, **k: pytest.fail('exact verified definition parsed again'))
    assert review_source_statement(obj) == raw.replace(b'CREATE ', b'CREATE OR REPLACE ', 1)


@pytest.mark.parametrize('kind,raw', [
    ('PROCEDURE', b'CREATE PROCEDURE APP.P IS BEGIN NULL; END;'),
    ('FUNCTION', b'CREATE FUNCTION APP.P RETURN NUMBER IS BEGIN RETURN 1; END;'),
    ('VIEW', b'CREATE VIEW APP.P AS SELECT 1 AS ID FROM DUAL;')])
def test_exact_replacement_emission_preserves_bytes_for_verified_units(monkeypatch, kind, raw):
    from types import SimpleNamespace
    from oracle_db_migration_generator.model.plan import SqlIntent
    from oracle_db_migration_generator.emission import sql
    obj = verified_source(raw, kind)
    statement = raw.replace(b'CREATE ', b'CREATE OR REPLACE ', 1)
    intent = SqlIntent(statement, 'SQL' if kind == 'VIEW' else 'PLSQL', 60,
                       verification_sha256=hashlib.sha256(statement).hexdigest())
    operation = SimpleNamespace(identity=obj.identity, kind='REPLACE', decision='READY',
                                operation_id='op-'+'a'*64, intent=intent)
    baseline = sql.render_statement(operation, 'fixed-plan')
    monkeypatch.setattr(sql, 'parse_ddl', lambda *a, **k: pytest.fail('verified SQL parsed again'))
    assert sql.render_statement(operation, 'fixed-plan', source=obj) == baseline
