"""Şema Karşılaştırma kaynak çözümlemesinin sırasını ve süreç yalıtımını sınar.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
from contextvars import ContextVar
import time

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
    selected = profile()
    artifacts = []
    for i in range(8):
        raw = f'CREATE TABLE APP.T{i}(ID NUMBER);'.encode()
        artifacts.append(SourceArtifact(f'app/t{i}.sql', 'APP', 'DDL', 'TABLE', raw,
                                        hashlib.sha256(raw).hexdigest()))
    inputs = SourceInput(SourceRevision('a'*40, None), tuple(artifacts), 'b'*64)
    monkeypatch.setenv('GENERATOR_PARSER_WORKERS', '1')
    serial = canonical_bytes(parse_source(inputs, selected).to_dict())
    monkeypatch.setenv('GENERATOR_PARSER_WORKERS', '4')
    parallel = canonical_bytes(parse_source(inputs, selected).to_dict())
    assert serial == parallel


@pytest.mark.parametrize('value', ['0', '9', 'invalid'])
def test_worker_count_rejects_invalid_configuration(monkeypatch, value):
    monkeypatch.setenv('GENERATOR_PARSER_WORKERS', value)
    with pytest.raises(ValueError, match='PARSER_WORKERS_INVALID'):
        client.parser_workers()
