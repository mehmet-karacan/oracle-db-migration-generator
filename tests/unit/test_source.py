import json
import subprocess
from pathlib import Path

import pytest

from oracle_db_migration_generator.config.loader import load_source_profile
from oracle_db_migration_generator.source.git_reader import GitRepository, read_source, resolve_source
from oracle_db_migration_generator.source.layout import collect_layout
from oracle_db_migration_generator.source.models import GitEntry, SourceError

ROOT = Path(__file__).resolve().parents[2]


def profile(tmp_path, layout='by_object'):
    data = json.loads((ROOT / 'examples/source-profile.example.json').read_text(encoding='utf-8'))
    data['layout'] = layout
    data['schema_roots'] = [{'path': 'app', 'source_schema': 'APP'}]
    path = tmp_path / 'profile.json'
    path.write_text(json.dumps(data), encoding='utf-8')
    return load_source_profile(path)


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL).decode().strip()


def commit(root, text):
    path = root / 'app/tables/DEMO/ddl.sql'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    git(root, 'add', 'app')
    git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=synthetic@example.invalid', 'commit', '-m', 'fixture')
    return git(root, 'rev-parse', 'HEAD')


def test_pinned_source_is_shared_by_all_targets(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    git(repo, 'init', '-b', 'main')
    before = commit(repo, 'CREATE TABLE APP.DEMO (ID NUMBER);')
    reader = GitRepository(repo)
    revision = resolve_source(reader, 'main')
    commit(repo, 'CREATE TABLE APP.DEMO (ID NUMBER, TITLE VARCHAR2(80 CHAR));')
    first = read_source(revision, profile(tmp_path))
    second = read_source(revision, profile(tmp_path))
    assert first.revision.commit == second.revision.commit == before
    assert first.input_digest == second.input_digest
    assert b'TITLE' not in first.artifacts[0].raw
    assert git(repo, 'status', '--porcelain') == ''


def entry(path, raw=b'SELECT 1;', mode='100644', kind='blob'):
    return GitEntry(path, mode, kind, 'a' * 40, raw)


def test_by_object_nested_children_and_sidecars(tmp_path):
    paths = ['app/tables/T/ddl.sql', 'app/tables/T/indexes/I.sql',
             'app/tables/T/triggers/TR.sql', 'app/tables/T/synonyms/S.sql',
             'app/tables/T/comments.sql', 'app/tables/T/grants.sql',
             'app/tables/T/dependencies.json']
    artifacts = collect_layout(tuple(entry(path) for path in paths), profile(tmp_path))
    assert {a.path for a in artifacts} == set(paths)
    assert {a.kind for a in artifacts} == {'DDL', 'COMMENT', 'GRANT', 'DEPENDENCIES'}
    assert all(a.source_schema == 'APP' for a in artifacts)
    assert next(a for a in artifacts if '/indexes/' in a.path).object_type_hint == 'INDEX'


def test_flat_combined_package_spec_body_is_one_preserved_input(tmp_path):
    raw = b'CREATE PACKAGE APP.P AS END;\n/\nCREATE PACKAGE BODY APP.P AS END;\n/\n'
    artifacts = collect_layout((entry('app/Packages/P.sql', raw),), profile(tmp_path, 'flat'))
    assert artifacts[0].raw == raw
    assert artifacts[0].object_type_hint == 'PACKAGE_SPEC'


def test_missing_source_root_is_not_empty_schema(tmp_path):
    with pytest.raises(SourceError, match='SOURCE_SCOPE_MISSING'):
        collect_layout((entry('other/tables/T/ddl.sql'),), profile(tmp_path))


@pytest.mark.parametrize('mode,kind,raw', [
    ('120000', 'blob', b'../../outside.sql'), ('160000', 'commit', b''),
    ('100644', 'blob', b'version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 10\n'),
    ('100644', 'blob', b'\x00binary'),
])
def test_symlink_submodule_and_lfs_are_not_sql(tmp_path, mode, kind, raw):
    with pytest.raises(SourceError):
        collect_layout((entry('app/tables/T/ddl.sql', raw, mode, kind),), profile(tmp_path))


def test_manifest_mismatch_and_unknown_layout_do_not_silently_fallback(tmp_path):
    manifest = json.dumps({'schema':'OTHER', 'layout':'by_object', 'layout_version':1}).encode()
    with pytest.raises(SourceError, match='SOURCE_MANIFEST_MISMATCH'):
        collect_layout((entry('app/_manifest.json', manifest),), profile(tmp_path))
    with pytest.raises(SourceError, match='SOURCE_LAYOUT_MISMATCH'):
        collect_layout((entry('app/unknown/T.sql'),), profile(tmp_path))
