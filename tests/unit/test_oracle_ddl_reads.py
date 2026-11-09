"""Şema Karşılaştırma paralel DDL okumalarında oturum ve hata sınırlarını sınar.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
import threading
from dataclasses import replace
import pytest

from oracle_db_migration_generator.config.credentials import Credentials
from oracle_db_migration_generator.oracle import collector
from tests.unit.test_collector import FakeConnection, FakeCursor, inputs


@pytest.mark.parametrize('workers', [4, 8])
def test_bounded_readers_have_private_read_only_sessions_and_equal_snapshot(monkeypatch, workers):
    connections = []
    barrier = threading.Barrier(workers, timeout=5)
    concurrent = [False]
    class Cursor(FakeCursor):
        """Her sahte Oracle oturumunun kendi iş parçacığında kullanılmasını denetler.

        Author: Mehmet KARACAN
        Date: 2026-11-06
        """
        def __init__(self):
            super().__init__(inventory=[('TABLE', f'T{i}', 'VALID', '2026-11-06') for i in range(12)])
            self.thread = threading.get_ident()
            self.first = True
        def execute(self, query, binds=None):
            assert threading.get_ident() == self.thread
            self.binds = binds
            if 'GET_DDL' in query.upper() and self.first and concurrent[0]:
                self.first = False
                barrier.wait()
            return super().execute(query, binds)
        def fetchone(self):
            if 'GET_DDL' in self.current.upper():
                return (f'CREATE TABLE APP.{self.binds["name"]}(ID NUMBER);',)
            return super().fetchone()
        def close(self):
            assert threading.get_ident() == self.thread
    def connect(*_):
        connection = FakeConnection()
        connection.reader = Cursor()
        connections.append(connection)
        return connection
    target, profile = inputs()
    monkeypatch.setenv('GENERATOR_ORACLE_DDL_WORKERS', '1')
    baseline = collector.collect_target(target, lambda _: Credentials('APP', 'synthetic'), profile, connect=connect)
    assert baseline.snapshot is not None
    connections.clear()
    concurrent[0] = True
    monkeypatch.setenv('GENERATOR_ORACLE_DDL_WORKERS', str(workers))
    captured = collector.collect_target(target, lambda _: Credentials('APP', 'synthetic'), profile, connect=connect)
    assert captured.snapshot is not None, captured.receipt
    assert len(connections) == workers + 1
    assert captured.snapshot.to_dict() == baseline.snapshot.to_dict()
    assert [(o.object_key, o.raw_ddl) for o in captured.snapshot.objects] == [(o.object_key, o.raw_ddl) for o in baseline.snapshot.objects]
    assert all(c.closed and c.rollbacks for c in connections)
    for c in connections:
        assert c.reader.calls[0][0] == collector.READ_ONLY_TRANSACTION
        assert all(sql == collector.READ_ONLY_TRANSACTION or sql.lstrip().upper().startswith('SELECT') for sql, _ in c.reader.calls)


def test_reader_identity_rejection_closes_every_session(monkeypatch):
    monkeypatch.setenv('GENERATOR_ORACLE_DDL_WORKERS', '4')
    connections = []
    class WrongCursor(FakeCursor):
        """Ek oturumun farklı bir kullanıcıyla açılmasını taklit eder.

        Author: Mehmet KARACAN
        Date: 2026-11-06
        """
        def fetchone(self):
            if 'SYS_CONTEXT' in self.current.upper(): return ('OTHER',)
            return super().fetchone()
    def connect(*_):
        c = FakeConnection(inventory=[('TABLE', 'DEMO', 'VALID', 'stamp')])
        if connections: c.reader = WrongCursor()
        connections.append(c)
        return c
    target, profile = inputs()
    result = collector.collect_target(target, lambda _: Credentials('APP', 'synthetic'), profile, connect=connect)
    assert result.snapshot is None
    assert all(c.closed for c in connections)
    assert all(not any('GET_DDL' in sql for sql, _ in c.reader.calls) for c in connections[1:])


def test_overlapping_read_intervals_are_counted_once():
    from oracle_db_migration_generator.oracle.ddl_reads import active_read_seconds
    assert active_read_seconds([(2., 5.), (7., 8.), (1., 3.)]) == 5.


@pytest.mark.parametrize('failure', ['read', 'cleanup', 'deadline'])
def test_parallel_failures_preserve_unknowns_and_close_sessions(monkeypatch, failure):
    connections = []
    class Cursor(FakeCursor):
        """DDL okuma ve bağlantı kapatma hatalarını taklit eder.

        Author: Mehmet KARACAN
        Date: 2026-11-06
        """
        def execute(self, query, binds=None):
            self.binds = binds
            super().execute(query, binds)
            if failure == 'read' and 'GET_DDL' in query and binds['name'] == 'T3':
                raise RuntimeError('ORA-01031: synthetic-secret')
        def fetchone(self):
            if 'GET_DDL' in self.current.upper(): return (f'CREATE TABLE APP.{self.binds["name"]}(ID NUMBER);',)
            return super().fetchone()
        def close(self):
            if failure == 'cleanup' and threading.get_ident() != threading.main_thread().ident:
                raise RuntimeError('synthetic close error')
    def connect(*_):
        c = FakeConnection()
        c.reader = Cursor(inventory=[('TABLE', f'T{i}', 'VALID', 'stamp') for i in range(10)])
        connections.append(c)
        return c
    target, profile = inputs()
    if failure == 'deadline': target = replace(target, capture_timeout_seconds=0)
    monkeypatch.setenv('GENERATOR_ORACLE_DDL_WORKERS', '4')
    captured = collector.collect_target(target, lambda _: Credentials('APP', 'synthetic'), profile, connect=connect)
    assert all(c.closed for c in connections)
    if failure == 'read':
        assert captured.snapshot is not None
        denied = next(o for o in captured.snapshot.objects if o.identity.name.effective_name == 'T3')
        assert denied.raw_ddl is None and denied.coverage.ddl == 'PARTIAL'
        assert denied.coverage.diagnostics == ('ORA-01031',)
        assert len(captured.snapshot.objects) == 10
    else:
        assert captured.snapshot is None
        expected = 'DDL_READER_CLEANUP_FAILED' if failure == 'cleanup' else 'TARGET_CAPTURE_TIMEOUT'
        assert captured.receipt['schemas'][0]['error_code'] == expected
