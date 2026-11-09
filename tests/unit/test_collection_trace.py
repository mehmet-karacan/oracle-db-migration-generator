"""Şema Karşılaştırma canlı kayıt aracının seri tekrarını sahte Oracle ile doğrular.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
import json
import pytest

from oracle_db_migration_generator.config.credentials import Credentials
from oracle_db_migration_generator.oracle.collector import collect_target
from tests.unit.test_collector import FakeConnection, FakeCursor, inputs
from tools.benchmark_oracle_collection import QueryTrace, TracedConnection, ReplayConnection


@pytest.mark.parametrize('denied', [None, 'ALL_TAB_COLS'])
def test_trace_replays_identical_metadata_and_safe_errors(monkeypatch, denied):
    trace = QueryTrace()
    class Cursor(FakeCursor):
        """Farklı iki tablonun gerçek parser tarafından okunacak DDL metnini verir.

        Author: Mehmet KARACAN
        Date: 2026-11-06
        """
        def execute(self, query, binds=None):
            self.binds = binds
            return super().execute(query, binds)
        def fetchone(self):
            if 'GET_DDL' in self.current.upper():return (f'CREATE TABLE APP.{self.binds["name"]}(ID NUMBER);',)
            return super().fetchone()
    def connect(*_):
        native = FakeConnection()
        native.reader = Cursor(inventory=[('TABLE', f'T{i}', 'VALID', 'fixed') for i in range(6)], denied=denied)
        return TracedConnection(native, trace)
    target, profile = inputs()
    monkeypatch.setenv('GENERATOR_ORACLE_DDL_WORKERS', '4')
    captured = collect_target(target, lambda _: Credentials('APP','synthetic-password'), profile, connect=connect)
    assert captured.snapshot is not None
    monkeypatch.setenv('GENERATOR_ORACLE_DDL_WORKERS', '1')
    replay = collect_target(target, lambda _: Credentials('APP','synthetic-password'), profile,
                            connect=lambda *_: ReplayConnection(trace, '19.0.0.0.0'))
    assert replay.snapshot is not None, replay.receipt
    assert captured.snapshot.to_dict() == replay.snapshot.to_dict()
    assert not trace.missing
    assert 'synthetic-password' not in json.dumps(trace.rows)
