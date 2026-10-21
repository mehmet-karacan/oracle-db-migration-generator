import copy
import json
from types import SimpleNamespace

import pytest

from oracle_db_migration_generator.parsing import client


def payload(raw=b'CREATE TABLE APP.T(ID NUMBER);', owner='APP'):
    return {'objects': [{'object_type': 'TABLE', 'raw_schema': owner, 'schema_quoted': False,
        'raw_name': 'T', 'name_quoted': False, 'start_char': 0, 'end_char': len(raw.decode()),
        'parse_ok': True, 'diagnostics': [], 'projection': {'$type': 'Projection', 'fields': {
            'object_key': 'test', 'object_type': 'TABLE', 'properties': {'columns': {}},
            'support': 'structural', 'diagnostics': {'$tuple': []}}}}], 'sidecars': [], 'diagnostics': []}


@pytest.fixture
def worker(monkeypatch, tmp_path):
    calls = []
    responses = []

    class Worker:
        process = SimpleNamespace(poll=lambda: None)

        def request(self, raw, owner, timeout, metadata=False):
            calls.append((raw, owner, metadata))
            return copy.deepcopy(responses.pop(0) if responses else payload(raw, owner))

        def close(self):
            pass

    monkeypatch.setattr(client, 'ParserClient', Worker)
    monkeypatch.setattr(client, '_client', None)
    monkeypatch.setenv('GENERATOR_PARSER_CACHE_DIR', str(tmp_path/'cache'))
    return calls, responses, tmp_path/'cache'


def test_exact_verified_response_avoids_worker_and_returns_independent_payload(worker):
    calls, _, _ = worker
    raw = b'CREATE TABLE APP.T(ID NUMBER);'
    first = client.request_parse(raw, 'APP')
    first['objects'][0]['projection']['fields']['properties']['columns']['INJECTED'] = True
    second = client.request_parse(raw, 'APP')
    assert len(calls) == 1
    assert second == payload(raw)
    client._client = None  # A newly started CLI may reuse only the exact verified bytes.
    assert client.request_parse(raw, 'APP') == second
    assert len(calls) == 1


def test_raw_owner_metadata_and_parser_artifact_are_independent_cache_inputs(worker, monkeypatch):
    from oracle_db_migration_generator.parsing import response_cache
    calls, _, _ = worker
    raw = b'CREATE TABLE APP.T(ID NUMBER);'
    monkeypatch.setattr(response_cache, 'parser_artifact_sha256', lambda: 'a'*64)
    client.request_parse(raw, 'APP')
    client.request_parse(raw+b' ', 'APP')
    client.request_parse(raw, 'OTHER')
    client.request_parse(raw, 'APP', metadata=True)
    monkeypatch.setattr(response_cache, 'parser_artifact_sha256', lambda: 'b'*64)
    client.request_parse(raw, 'APP')
    assert len(calls) == 5


@pytest.mark.parametrize('diagnostic', ['PARSER_SYNTAX_ERROR', 'PARSER_TIMEOUT'])
def test_unverified_results_are_never_reused(worker, diagnostic):
    calls, responses, root = worker
    failed = {'objects': [], 'sidecars': [], 'diagnostics': [diagnostic]}
    responses.extend([failed, failed])
    assert client.request_parse(b'bad input', 'APP') == failed
    assert client.request_parse(b'bad input', 'APP') == failed
    assert len(calls) == 2 and not list(root.rglob('*.json'))


@pytest.mark.parametrize('change', ['hash', 'shape', 'input'])
def test_tampered_response_or_context_is_a_fresh_parse(worker, change):
    from oracle_db_migration_generator.parsing.response_cache import json_bytes
    import hashlib
    calls, _, root = worker
    raw = b'CREATE TABLE APP.T(ID NUMBER);'
    expected = client.request_parse(raw, 'APP')
    path = next(root.rglob('*.json'))
    document = json.loads(path.read_bytes())
    if change == 'input':
        document['input']['default_schema'] = 'OTHER'
    else:
        document['payload']['objects'][0]['extra'] = 'unrecognized'
        if change == 'shape':
            document['payload_sha256'] = hashlib.sha256(json_bytes(document['payload'])).hexdigest()
    path.write_bytes(json_bytes(document))
    assert client.request_parse(raw, 'APP') == expected
    assert len(calls) == 2


def test_disabled_or_unusable_cache_preserves_fresh_parser_behavior(worker, monkeypatch, tmp_path):
    calls, _, _ = worker
    raw = b'CREATE TABLE APP.T(ID NUMBER);'
    monkeypatch.delenv('GENERATOR_PARSER_CACHE_DIR')
    client.request_parse(raw, 'APP'); client.request_parse(raw, 'APP')
    bad = tmp_path/'file'; bad.write_text('occupied')
    monkeypatch.setenv('GENERATOR_PARSER_CACHE_DIR', str(bad))
    client.request_parse(raw, 'APP'); client.request_parse(raw, 'APP')
    assert len(calls) == 4 and bad.read_text() == 'occupied'


def test_symlinked_cache_ancestor_is_never_read_or_written(worker, monkeypatch):
    from pathlib import Path
    calls, _, root = worker
    root.mkdir()
    original = Path.is_symlink
    monkeypatch.setattr(Path, 'is_symlink', lambda path: path == root or original(path))
    raw = b'CREATE TABLE APP.T(ID NUMBER);'
    client.request_parse(raw, 'APP'); client.request_parse(raw, 'APP')
    assert len(calls) == 2 and list(root.iterdir()) == []


def test_windows_reparse_cache_ancestor_is_not_followed(worker, monkeypatch):
    from pathlib import Path
    calls, _, root = worker
    root.mkdir()
    original = Path.lstat

    def reparse(path, *args, **kwargs):
        value = original(path, *args, **kwargs)
        return SimpleNamespace(st_mode=value.st_mode, st_file_attributes=0x400) if path == root else value

    monkeypatch.setattr(Path, 'lstat', reparse)
    raw = b'CREATE TABLE APP.T(ID NUMBER);'
    client.request_parse(raw, 'APP'); client.request_parse(raw, 'APP')
    assert len(calls) == 2 and list(root.iterdir()) == []


def test_failed_atomic_cache_publication_leaves_no_partial_entry(worker, monkeypatch):
    from oracle_db_migration_generator.parsing import response_cache
    calls, _, root = worker
    original = response_cache.os.replace

    def failed_publish(source, destination):
        if str(destination).endswith('.json'):
            raise OSError('synthetic cache disk failure')
        return original(source, destination)

    monkeypatch.setattr(response_cache.os, 'replace', failed_publish)
    raw = b'CREATE TABLE APP.T(ID NUMBER);'
    assert client.request_parse(raw, 'APP') == client.request_parse(raw, 'APP')
    assert len(calls) == 2 and not list(root.rglob('*.json')) and not list(root.rglob('.tmp-*'))


def test_bucket_limits_evict_only_cache_entries_and_keep_complete_atomic_files(worker, monkeypatch):
    from oracle_db_migration_generator.parsing import response_cache
    calls, _, root = worker
    monkeypatch.setattr(response_cache, 'MAX_BUCKET_ENTRIES', 2)
    monkeypatch.setattr(response_cache, 'MAX_BUCKET_BYTES', 2400)
    by_bucket = {}
    for number in range(2000):
        raw = b'CREATE TABLE APP.T(ID NUMBER); --'+str(number).encode()
        entry = response_cache.ParserResponseCache(str(root), raw, 'APP', False)
        selected = by_bucket.setdefault(entry.bucket, [])
        selected.append(raw)
        if len(selected) == 3:
            break
    assert len(selected) == 3
    for raw in selected:
        client.request_parse(raw, 'APP')
    paths = list(entry.bucket.glob('*.json'))
    assert 0 < len(paths) <= 2
    assert sum(path.stat().st_size for path in paths) <= 2400
    assert not list(root.rglob('.tmp-*'))
    assert all(json.loads(path.read_bytes())['schema_version'] == 'parser-response-cache/1.0' for path in paths)
    assert len(calls) == 3


def test_oversized_or_unverified_object_projection_is_not_cached(worker, monkeypatch):
    from oracle_db_migration_generator.parsing import response_cache
    calls, responses, root = worker
    raw = b'CREATE TABLE APP.T(ID NUMBER);'
    bad = payload(raw)
    bad['objects'][0]['projection']['fields']['diagnostics'] = {'$tuple': ['UNSUPPORTED']}
    responses.extend([bad, bad])
    client.request_parse(raw, 'APP'); client.request_parse(raw, 'APP')
    assert not list(root.rglob('*.json'))
    monkeypatch.setattr(response_cache, 'MAX_ENTRY_BYTES', 5)
    client.request_parse(raw, 'APP'); client.request_parse(raw, 'APP')
    assert len(calls) == 4 and not list(root.rglob('*.json'))


def test_real_parser_cached_result_preserves_projection_identity_coverage_and_utf8_spans(monkeypatch, tmp_path):
    from oracle_db_migration_generator.model.identity import Identifier, ObjectIdentity
    from oracle_db_migration_generator.parsing.adapter import parse_ddl
    raw = 'CREATE TABLE APP."Türkçe" ("İD" NUMBER DEFAULT 1 NOT NULL);'.encode('utf-8')
    identity = ObjectIdentity('test', Identifier.parse('APP'), 'TABLE', Identifier.parse('"Türkçe"'))
    calls = []
    original = client.ParserClient.request

    def request(self, *args, **kwargs):
        calls.append(True)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(client.ParserClient, 'request', request)
    monkeypatch.setenv('GENERATOR_PARSER_CACHE_DIR', str(tmp_path/'real-cache'))
    first = parse_ddl(raw, identity)
    second = parse_ddl(raw, identity)
    assert first.coverage == 'COMPLETE' and first.objects[0].identity == identity
    assert first == second and first.objects[0].raw_ddl == raw
    assert first.objects[0].end_byte == len(raw)
    assert len(calls) == 1


@pytest.mark.parametrize(('path', 'value'), [
    (('properties',), None),
    (('properties', 'columns'), None),
    (('properties', 'columns'), {'U:ID': None}),
    (('properties', 'columns'), {'U:ID': {'data_type': 7}}),
    (('properties', 'routines'), {'$tuple': ['arbitrary routine']}),
    (('properties', '_generator_inline_backing_keys'), [{'column': None}]),
    (('object_type',), 'VIEW'),
    (('object_type',), None),
    (('support',), []),
    (('support',), 'text_fallback'),
])
def test_semantically_malformed_projection_is_a_cache_miss_even_with_matching_hash(worker, path, value):
    from oracle_db_migration_generator.parsing.response_cache import json_bytes
    import hashlib
    calls, _, root = worker
    raw = b'CREATE TABLE APP.T(ID NUMBER);'
    expected = client.request_parse(raw, 'APP')
    cache_file = next(root.rglob('*.json'))
    document = json.loads(cache_file.read_bytes())
    target = document['payload']['objects'][0]['projection']['fields']
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    document['payload_sha256'] = hashlib.sha256(json_bytes(document['payload'])).hexdigest()
    cache_file.write_bytes(json_bytes(document))
    assert client.request_parse(raw, 'APP') == expected
    assert len(calls) == 2


@pytest.mark.parametrize(('nested', 'field', 'value'), [
    ('Routine', 'start_line', '1'),
    ('Parameter', 'nocopy', 'false'),
    ('Parameter', 'data_type', {}),
    ('DynamicSqlProfile', 'bind', 'false'),
])
def test_wrong_nested_dataclass_field_type_is_a_cache_miss(worker, nested, field, value):
    import hashlib
    from oracle_db_migration_generator.parsing.codec import encode
    from oracle_db_migration_generator.parsing.response_cache import json_bytes
    from oracle_db_migration_generator._vendor.analyzer_core.oracle.package import Routine, Parameter
    from oracle_db_migration_generator._vendor.analyzer_core.oracle.dynamic_sql import DynamicSqlProfile
    calls, _, root = worker
    raw = b'CREATE TABLE APP.T(ID NUMBER);'
    expected = client.request_parse(raw, 'APP')
    routine = Routine('R', 'PROCEDURE', 'R(P IN NUMBER)', None,
        (Parameter('P', 1, 'IN', 'NUMBER', None, False, 'P IN NUMBER'),),
        'PROCEDURE R;', 1, 1, (), (), (),
        (DynamicSqlProfile('unknown', 'unknown', False, False),), (), (), (), (), (), ())
    encoded = encode(routine)
    target = encoded['fields']
    if nested == 'Parameter':
        target = target['parameters']['$tuple'][0]['fields']
    elif nested == 'DynamicSqlProfile':
        target = target['dynamic_sql_profiles']['$tuple'][0]['fields']
    target[field] = value
    cache_file = next(root.rglob('*.json'))
    document = json.loads(cache_file.read_bytes())
    document['payload']['objects'][0]['projection']['fields']['properties']['routines'] = {'$tuple': [encoded]}
    document['payload_sha256'] = hashlib.sha256(json_bytes(document['payload'])).hexdigest()
    cache_file.write_bytes(json_bytes(document))
    assert client.request_parse(raw, 'APP') == expected
    assert len(calls) == 2
