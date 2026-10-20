import hashlib
import json
from pathlib import Path

import pytest

from oracle_db_migration_generator.config.loader import load_source_profile
from oracle_db_migration_generator.model.snapshot_io import load_snapshot, write_source_snapshot
from oracle_db_migration_generator.parsing.adapter import parse_source
from oracle_db_migration_generator.source.models import SourceArtifact, SourceInput, SourceRevision

ROOT = Path(__file__).resolve().parents[2]


def test_source_snapshot_roundtrip_preserves_full_ddl_and_evidence(tmp_path):
    profile = load_source_profile(ROOT/'examples/source-profile.example.json')
    raw = b'CREATE TABLE APP.DEMO (ID NUMBER, TITLE VARCHAR2(80 CHAR));\n'
    artifact = SourceArtifact('app/tables/DEMO/ddl.sql','APP','DDL','TABLE',raw,hashlib.sha256(raw).hexdigest())
    inputs = SourceInput(SourceRevision('a'*40,None),(artifact,),'b'*64)
    snapshot = parse_source(inputs,profile)
    root = tmp_path/'prepared'
    path = write_source_snapshot(snapshot,inputs,root)
    loaded = load_snapshot(path)
    assert loaded.to_dict()==snapshot.to_dict()
    assert loaded.objects[0].raw_ddl==snapshot.objects[0].raw_ddl
    assert (root/artifact.path).read_bytes()==raw
    marker = root/'keep.txt'; marker.write_text('keep',encoding='utf-8')
    with pytest.raises(ValueError,match='OUTPUT_ALREADY_EXISTS'):
        write_source_snapshot(snapshot,inputs,root)
    assert marker.read_text(encoding='utf-8')=='keep'


def test_snapshot_identity_tamper_and_ddl_tamper_are_rejected(tmp_path):
    profile = load_source_profile(ROOT/'examples/source-profile.example.json')
    raw = b'CREATE TABLE APP.DEMO (ID NUMBER);'
    artifact = SourceArtifact('app/tables/DEMO/ddl.sql','APP','DDL','TABLE',raw,hashlib.sha256(raw).hexdigest())
    inputs = SourceInput(SourceRevision('a'*40,None),(artifact,),'b'*64)
    snapshot = parse_source(inputs,profile)
    path = write_source_snapshot(snapshot,inputs,tmp_path/'prepared')
    document = json.loads(path.read_text(encoding='utf-8'))
    document['objects'][0]['identity']['name'] = 'OTHER'
    path.write_text(json.dumps(document),encoding='utf-8')
    with pytest.raises(ValueError,match='SNAPSHOT_IDENTITY_MISMATCH'):
        load_snapshot(path)
    path.write_text(json.dumps(snapshot.to_dict()),encoding='utf-8')
    (path.parent/artifact.path).write_bytes(raw+b' DROP TABLE APP.OTHER;')
    with pytest.raises(ValueError,match='SNAPSHOT_DDL_INTEGRITY_MISMATCH'):
        load_snapshot(path)
