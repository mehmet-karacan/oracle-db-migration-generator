"""Şema Karşılaştırma hedef çözümlemesinin sırasını ve oturum sahipliğini sınar.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
from contextvars import ContextVar
import threading

from oracle_db_migration_generator.config.credentials import Credentials
from oracle_db_migration_generator.oracle import collector
from tests.unit.test_collector import FakeConnection, FakeCursor, inputs


class OwnedCursor(FakeCursor):
    def __init__(self):
        super().__init__(inventory=[('TABLE',f'T{i}','VALID','2026-11-06') for i in range(6)])
        self.owner=threading.get_ident()
        self.closed=False

    def execute(self,query,binds=None):
        assert threading.get_ident()==self.owner
        self.binds=binds
        return super().execute(query,binds)

    def fetchone(self):
        assert threading.get_ident()==self.owner
        if 'GET_DDL' in self.current.upper():
            name=self.binds['name']
            sql=f'CREATE TABLE APP.{name} (ID NUMBER);'
            if name=='T0':
                sql+=' ALTER TABLE APP.T0 ADD CONSTRAINT T0_PK PRIMARY KEY (ID);'
            return (sql,)
        return super().fetchone()

    def fetchall(self):
        assert threading.get_ident()==self.owner
        return super().fetchall()

    def close(self):
        assert threading.get_ident()==self.owner
        self.closed=True


def capture():
    target,profile=inputs()
    connection=FakeConnection()
    connection.reader=OwnedCursor()
    result=collector.collect_target(target,lambda _:Credentials('APP','synthetic'),profile,
                                    connect=lambda *_:connection)
    return result,connection


def test_parallel_projection_preserves_snapshot_evidence_and_cursor_thread(monkeypatch):
    monkeypatch.setenv('GENERATOR_PARSER_WORKERS','1')
    serial,first=capture()
    assert serial.snapshot is not None
    assert any('context statement' in ev.detail_tr for ev in serial.snapshot.evidence)
    real=collector.project_target_object
    context=ContextVar('collector_test_context',default=None)
    token=context.set('copied')
    threads=set()
    barrier=threading.Barrier(3,timeout=10)
    def projected(item):
        assert context.get()=='copied'
        threads.add(threading.get_ident())
        barrier.wait()
        return real(item)
    monkeypatch.setattr(collector,'project_target_object',projected)
    monkeypatch.setenv('GENERATOR_PARSER_WORKERS','3')
    try:
        parallel,second=capture()
    finally:
        context.reset(token)
    assert parallel.snapshot is not None
    assert len(threads)==3 and threading.get_ident() not in threads
    assert parallel.snapshot.to_dict()==serial.snapshot.to_dict()
    assert [(o.object_key,o.raw_ddl) for o in parallel.snapshot.objects]==[(o.object_key,o.raw_ddl) for o in serial.snapshot.objects]
    assert first.reader.calls==second.reader.calls
    assert first.closed and second.closed and second.reader.closed


def test_projection_exception_closes_cursor_and_connection(monkeypatch):
    monkeypatch.setenv('GENERATOR_PARSER_WORKERS','3')
    def fail(_):
        raise ValueError('synthetic failure')
    monkeypatch.setattr(collector,'project_target_object',fail)
    result,connection=capture()
    assert result.snapshot is None and result.receipt['status']=='ERROR'
    assert connection.closed and connection.reader.closed and connection.rollbacks>=1


def test_slow_first_projection_does_not_stop_later_work(monkeypatch):
    monkeypatch.setenv('GENERATOR_PARSER_WORKERS', '3')
    monkeypatch.setenv('GENERATOR_ORACLE_DDL_WORKERS', '1')
    connection = FakeConnection()
    connection.reader = OwnedCursor()
    connection.reader.inventory = [('TABLE', f'T{i}', 'VALID', 'stamp') for i in range(12)]
    last = threading.Event()
    real = collector.project_target_object
    def project(obj):
        name = obj.identity.name.effective_name
        if name == 'T0': assert last.wait(8), 'first result stopped the queue'
        if name == 'T11': last.set()
        return real(obj)
    monkeypatch.setattr(collector, 'project_target_object', project)
    target, profile = inputs()
    captured = collector.collect_target(target, lambda _: Credentials('APP', 'synthetic'), profile,
                                       connect=lambda *_: connection)
    assert captured.snapshot is not None and last.is_set()
    assert len(captured.snapshot.objects) == 12
