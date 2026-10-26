import hashlib
import json
from dataclasses import replace

import pytest

from oracle_db_migration_generator.model.serialization import canonical_bytes
from oracle_db_migration_generator.source.git_reader import GitRepository, read_source, resolve_source
from tests.unit.test_jenkins_source_reuse import prepared_case


def case(tmp_path, *, partial=False):
    from oracle_db_migration_generator.source.prepared_cache import PreparedSourceCache
    repo, sha, profile, snapshot, _, _ = prepared_case(tmp_path, partial=partial)
    inputs = read_source(resolve_source(GitRepository(repo), sha), profile)
    return inputs, snapshot, PreparedSourceCache(tmp_path/'cache', inputs)


@pytest.mark.parametrize('partial', [False, True])
def test_completed_preparation_checkpoint_preserves_all_facts_and_unknowns(tmp_path, monkeypatch, partial):
    inputs, snapshot, cache = case(tmp_path, partial=partial)
    assert cache.load() is None
    assert cache.store(snapshot) is True
    monkeypatch.setattr('oracle_db_migration_generator.parsing.adapter.parse_source',
                        lambda *a, **kw: pytest.fail('Exact prepared input must not parse again'))
    monkeypatch.setattr('oracledb.connect', lambda *a, **kw: pytest.fail('No Oracle access'))
    restored = cache.load()
    assert canonical_bytes(restored.to_dict()) == canonical_bytes(snapshot.to_dict())
    assert restored.completeness == snapshot.completeness
    assert {obj.object_key: obj.raw_ddl for obj in restored.objects} == {
        obj.object_key: obj.raw_ddl for obj in snapshot.objects}


@pytest.mark.parametrize('change', ['bytes', 'commit', 'profile', 'preparation_code'])
def test_every_preparation_input_change_invalidates_checkpoint(tmp_path, monkeypatch, change):
    from oracle_db_migration_generator.source import prepared_cache
    inputs, snapshot, cache = case(tmp_path)
    assert cache.store(snapshot)
    if change == 'bytes':
        item=inputs.artifacts[0];raw=item.raw+b'\n'
        inputs=replace(inputs, artifacts=(replace(item, raw=raw, sha256=hashlib.sha256(raw).hexdigest()),))
    elif change == 'commit':
        inputs=replace(inputs, revision=replace(inputs.revision, commit='0'*40))
    elif change == 'profile':
        inputs=replace(inputs, profile=replace(inputs.profile, source_length_semantics='BYTE'))
    else:
        monkeypatch.setattr(prepared_cache, 'preparation_artifact_sha256', lambda: '0'*64)
    changed=prepared_cache.PreparedSourceCache(cache.root, inputs)
    assert changed.key != cache.key
    assert changed.load() is None


@pytest.mark.parametrize('damage', ['snapshot', 'raw', 'input', 'profile', 'manifest', 'deep_manifest', 'extra_file'])
def test_corrupt_or_unexpected_cache_never_becomes_a_source_result(tmp_path, damage):
    inputs, snapshot, cache = case(tmp_path)
    assert cache.store(snapshot)
    path=cache.path
    if damage == 'snapshot':
        target=path/'source-snapshot.json';doc=json.loads(target.read_bytes())
        doc['objects']=[];target.write_text(json.dumps(doc))
    elif damage == 'raw':
        (path/inputs.artifacts[0].path).write_bytes(b'CREATE TABLE APP.OTHER(ID NUMBER);')
    elif damage == 'input': (path/'source-input.json').write_text('{}')
    elif damage == 'profile': (path/'source-profile.json').write_text('{}')
    elif damage == 'manifest': (path/'prepared-cache.json').write_text('{')
    elif damage == 'deep_manifest':
        import sys
        depth=sys.getrecursionlimit()+100
        (path/'prepared-cache.json').write_text('['*depth+'0'+']'*depth)
    else: (path/'unexpected.sql').write_text('SELECT 1 FROM DUAL;')
    assert cache.load() is None


def test_cache_cannot_store_a_snapshot_bound_to_other_source_inputs(tmp_path):
    inputs, snapshot, cache = case(tmp_path)
    assert cache.store(replace(snapshot, source_commit='0'*40)) is False
    assert cache.load() is None


def test_decoder_recursion_failure_is_a_checkpoint_miss(tmp_path, monkeypatch):
    from oracle_db_migration_generator.source import prepared_cache
    _, snapshot, cache=case(tmp_path)
    assert cache.store(snapshot)
    def recursive_decode(_):
        raise RecursionError('decoder recursion limit')
    monkeypatch.setattr(prepared_cache.json, 'loads', recursive_decode)
    assert cache.load() is None


def test_cache_capacity_is_bounded_without_deleting_existing_entries(tmp_path, monkeypatch):
    from oracle_db_migration_generator.source import prepared_cache
    inputs, snapshot, cache = case(tmp_path)
    assert cache.store(snapshot)
    before={p.relative_to(cache.path).as_posix():p.read_bytes() for p in cache.path.rglob('*') if p.is_file()}
    monkeypatch.setattr(prepared_cache, 'MAX_CACHE_ENTRIES', 1)
    monkeypatch.setattr(prepared_cache, 'preparation_artifact_sha256', lambda: '0'*64)
    another=prepared_cache.PreparedSourceCache(cache.root, inputs)
    assert another.store(snapshot) is False
    assert before == {p.relative_to(cache.path).as_posix():p.read_bytes() for p in cache.path.rglob('*') if p.is_file()}


def test_cli_rechecks_git_but_does_not_reparse_identical_completed_preparation(tmp_path, monkeypatch):
    from oracle_db_migration_generator.cli import main
    from oracle_db_migration_generator.parsing import adapter
    inputs, snapshot, cache = case(tmp_path)
    repo=inputs.revision.repository.path
    monkeypatch.setenv('GENERATOR_PREPARED_SOURCE_CACHE_DIR', str(cache.root))
    first=tmp_path/'first';second=tmp_path/'second'
    args=['prepare-source','--repo',str(repo),'--ref',inputs.revision.commit,
          '--source-profile',str(tmp_path/'profile.json')]
    assert main([*args,'--output',str(first)]) == 0
    monkeypatch.setattr(adapter, 'parse_source', lambda *a, **kw: pytest.fail('Identical input was parsed twice'))
    assert main([*args,'--output',str(second)]) == 0
    for relative in ['source-snapshot.json','source-input.json','source-profile.json',inputs.artifacts[0].path]:
        assert (first/relative).read_bytes() == (second/relative).read_bytes()
    proof=json.loads((second/'preparation-performance.json').read_bytes())
    assert proof['cache_status'] == 'HIT_VERIFIED'
    assert proof['phases_seconds']['parse'] == 0
    assert proof['database_connections'] == 0 and proof['source_files'] == 1


def test_checkpoint_never_writes_inside_source_repository(tmp_path):
    from oracle_db_migration_generator.source.prepared_cache import PreparedSourceCache
    inputs, snapshot, _ = case(tmp_path)
    root=inputs.revision.repository.path/'forbidden-cache'
    cache=PreparedSourceCache(root,inputs)
    assert cache.store(snapshot) is False
    assert not root.exists()
    assert cache.load() is None


def test_partial_object_and_timeout_diagnostics_are_preserved_as_unknown(tmp_path):
    from oracle_db_migration_generator.model.snapshot import Coverage, KnownValue
    inputs, snapshot, cache = case(tmp_path)
    original=snapshot.objects[0]
    props={**original.properties, 'projection':KnownValue('UNKNOWN',None,original.evidence_ids),
           'definition':KnownValue('UNKNOWN',None,original.evidence_ids)}
    coverage=Coverage('COMPLETE','PARTIAL','NOT_APPLICABLE',('PARSER_TIMEOUT',))
    snapshot=replace(snapshot,objects=(replace(original,properties=props,coverage=coverage),),
                     completeness=coverage)
    assert cache.store(snapshot)
    restored=cache.load()
    assert restored.objects[0].properties['projection'].state == 'UNKNOWN'
    assert restored.objects[0].coverage.diagnostics == ('PARSER_TIMEOUT',)
    assert canonical_bytes(restored.to_dict()) == canonical_bytes(snapshot.to_dict())
