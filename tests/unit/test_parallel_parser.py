"""Şema Karşılaştırma kaynak çözümlemesinin sırasını ve süreç yalıtımını sınar.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
from contextvars import ContextVar
from contextlib import contextmanager
import time
import threading

import pytest

from oracle_db_migration_generator.parsing import client


def test_parallel_real_parser_matches_serial_and_closes_children(monkeypatch):
    monkeypatch.delenv('GENERATOR_PARSER_CACHE_DIR', raising=False)
    inputs = [f'CREATE TABLE APP.T{i}(ID NUMBER, NAME VARCHAR2(30));'.encode() for i in range(8)]
    def parse(raw):
        return client.request_parse(raw, 'APP')
    expected = [parse(raw) for raw in inputs]
    children = []
    original = client.ParserClient.__init__
    def started(self):
        original(self)
        children.append(self)
    monkeypatch.setattr(client.ParserClient, '__init__', started)
    with client.parallel_parser_map(parse, inputs, workers=3) as results:
        assert list(results) == expected
    assert 1 <= len(children) <= 3
    assert all(child.process.poll() is not None for child in children)


def test_parallel_order_context_and_failure_cleanup(monkeypatch):
    marker = ContextVar('test_marker', default='missing')
    marker.set('runtime-settings')
    def action(value):
        time.sleep((5-value)*0.005)
        return value, marker.get()
    with client.parallel_parser_map(action, range(6), workers=3) as results:
        assert list(results) == [(value, 'runtime-settings') for value in range(6)]


def test_completed_jobs_refill_pool_while_first_job_is_blocked():
    reached_later_job = threading.Event()
    def action(value):
        if value == 0:
            assert reached_later_job.wait(3), 'First job blocked new submissions'
        if value == 10:
            reached_later_job.set()
        return value
    with client.parallel_parser_map(action, range(20), workers=2, ordered=False) as results:
        values = list(results)
    assert sorted(values) == list(range(20))
    assert values[0] != 0


def test_timeout_only_discards_its_own_worker(monkeypatch):
    original = client.ParserClient.request
    children = []
    def request(self, raw, owner, timeout, metadata=False):
        if self not in children:
            children.append(self)
        if raw == b'timeout':
            self.close()
            raise TimeoutError('PARSER_TIMEOUT')
        return original(self, raw, owner, timeout, metadata)
    monkeypatch.setattr(client.ParserClient, 'request', request)
    monkeypatch.delenv('GENERATOR_PARSER_CACHE_DIR', raising=False)
    def parse(raw):
        try:
            return client.request_parse(raw, 'APP')['diagnostics']
        except TimeoutError:
            return ['PARSER_TIMEOUT']
    sql = b'CREATE TABLE APP.T(ID NUMBER);'
    with client.parallel_parser_map(parse, [sql, b'timeout', sql, sql], workers=2) as results:
        assert list(results) == [[], ['PARSER_TIMEOUT'], [], []]
    assert all(child.process.poll() is not None for child in children)


def test_source_snapshot_bytes_match_across_worker_counts(monkeypatch):
    import hashlib
    from oracle_db_migration_generator.model.serialization import canonical_bytes
    from oracle_db_migration_generator.parsing.adapter import parse_source
    from oracle_db_migration_generator.source.models import SourceArtifact, SourceInput, SourceRevision
    from tests.factories import profile
    from oracle_db_migration_generator.parsing import adapter
    selected = profile()
    artifacts = []
    for i in range(8):
        raw = f'CREATE TABLE APP.T{i}(ID NUMBER);'.encode()
        artifacts.append(SourceArtifact(f'app/t{i}.sql', 'APP', 'DDL', 'TABLE', raw,
                                        hashlib.sha256(raw).hexdigest()))
    for kind, raw in [('MANIFEST', b'{}'), ('DEPENDENCIES',
            b'{"schema":"APP","object":{"name":"T0","type":"TABLE"},"depends_on":[]}')]:
        artifacts.append(SourceArtifact(f'app/{kind}.json', 'APP', kind, None, raw,
                                        hashlib.sha256(raw).hexdigest()))
    inputs = SourceInput(SourceRevision('a'*40, None), tuple(artifacts), 'b'*64)
    monkeypatch.setenv('GENERATOR_PARSER_WORKERS', '1')
    serial = canonical_bytes(parse_source(inputs, selected).to_dict())
    monkeypatch.setenv('GENERATOR_PARSER_WORKERS', '4')
    original = adapter.parallel_parser_map
    @contextmanager
    def checked_map(function, items, **kwargs):
        assert all(item.kind == 'DDL' for item in items)
        assert kwargs['ordered'] is False
        with original(function, items, **kwargs) as results:
            yield results
    monkeypatch.setattr(adapter, 'parallel_parser_map', checked_map)
    progress = []
    parallel = canonical_bytes(parse_source(inputs, selected,
        progress=lambda count, total: progress.append((count, total))).to_dict())
    assert serial == parallel
    assert progress == [(count, 10) for count in range(2, 11)]


@pytest.mark.parametrize('value', ['0', '9', 'invalid'])
def test_worker_count_rejects_invalid_configuration(monkeypatch, value):
    monkeypatch.setenv('GENERATOR_PARSER_WORKERS', value)
    with pytest.raises(ValueError, match='PARSER_WORKERS_INVALID'):
        client.parser_workers()


def test_source_schedules_normal_files_before_packages_without_changing_snapshot(monkeypatch):
    import hashlib
    from oracle_db_migration_generator.model.serialization import canonical_bytes
    from oracle_db_migration_generator.parsing import adapter
    from oracle_db_migration_generator.source.models import SourceArtifact, SourceInput, SourceRevision
    from tests.factories import profile
    statements = [
        ('large', 'PACKAGE_BODY', 'CREATE OR REPLACE PACKAGE BODY APP.PB IS PROCEDURE P IS BEGIN NULL; END; END;\n--'+'x'*100),
        ('spec', 'PACKAGE_SPEC', 'CREATE OR REPLACE PACKAGE APP.PB IS PROCEDURE P; END;'),
        ('table', 'TABLE', 'CREATE TABLE APP.T(ID NUMBER);'),
        ('small', 'PACKAGE_BODY', 'CREATE OR REPLACE PACKAGE BODY APP.PA IS PROCEDURE P IS BEGIN NULL; END; END;'),
        ('function', 'FUNCTION', 'CREATE FUNCTION APP.F RETURN NUMBER IS BEGIN RETURN 1; END;'),
    ]
    artifacts = tuple(SourceArtifact(f'app/{name}.sql', 'APP', 'DDL', kind, sql.encode(),
        hashlib.sha256(sql.encode()).hexdigest()) for name, kind, sql in statements)
    inputs = SourceInput(SourceRevision('a'*40, None), artifacts, 'b'*64)
    original = adapter.parallel_parser_map
    @contextmanager
    def original_order(function, items, **kwargs):
        with original(function, artifacts, **kwargs) as results:
            yield results
    monkeypatch.setattr(adapter, 'parallel_parser_map', original_order)
    expected = canonical_bytes(adapter.parse_source(inputs, profile()).to_dict())
    observed = []
    @contextmanager
    def scheduled(function, items, **kwargs):
        observed.extend(item.path for item in items)
        with original(function, items, **kwargs) as results:
            yield results
    monkeypatch.setattr(adapter, 'parallel_parser_map', scheduled)
    actual = canonical_bytes(adapter.parse_source(inputs, profile()).to_dict())
    assert observed == ['app/table.sql', 'app/function.sql', 'app/large.sql', 'app/small.sql', 'app/spec.sql']
    assert actual == expected
