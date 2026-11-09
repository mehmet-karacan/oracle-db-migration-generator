"""Şema Karşılaştırma kaynak arşivinde büyük ve küçük harfli yolları sınar.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
import hashlib
import pytest

from oracle_db_migration_generator.model.serialization import digest
from oracle_db_migration_generator.parsing.adapter import parse_source
from oracle_db_migration_generator.source.models import SourceArtifact, SourceInput, SourceRevision
from oracle_db_migration_generator.source.prepared_cache import PreparedSourceCache
from tests.factories import profile


@pytest.mark.parametrize('second_file', ['ddl.sql', 'other.sql'])
def test_case_distinct_git_paths_survive_cache_and_snapshot_roundtrip(tmp_path, second_file):
    selected = profile()
    artifacts = tuple(SourceArtifact(path, 'APP', 'DDL', 'TABLE', sql, hashlib.sha256(sql).hexdigest())
        for path, sql in [('app/tables/T/ddl.sql', b'CREATE TABLE APP.T(ID NUMBER);'),
                          ('app/tables/t/'+second_file, b'CREATE TABLE APP."t"(TITLE VARCHAR2(80));')])
    commit = 'a'*40
    fingerprint = digest({'commit': commit, 'profile': selected,
                          'files': [[a.path, a.kind, a.sha256] for a in artifacts]})
    inputs = SourceInput(SourceRevision(commit, None), artifacts, fingerprint, selected)
    snapshot = parse_source(inputs, selected)
    cache = PreparedSourceCache(tmp_path/'cache', inputs)
    assert cache.store(snapshot)
    restored = cache.load()
    assert restored is not None
    assert restored.to_dict() == snapshot.to_dict()
    assert {obj.identity.name.effective_name: obj.raw_ddl for obj in restored.objects} == {
        obj.identity.name.effective_name: obj.raw_ddl for obj in snapshot.objects}
    blob = next((cache.path/'source-blobs').glob('*.bin'))
    blob.write_bytes(b'altered')
    assert cache.load() is None
