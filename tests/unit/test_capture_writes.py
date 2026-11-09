"""Şema Karşılaştırma arşiv yazımının paralelliğini ve byte eşitliğini sınar.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
from dataclasses import replace
import hashlib
from pathlib import Path
import threading

from oracle_db_migration_generator.model.evidence import Evidence
from oracle_db_migration_generator.model.identity import Identifier, ObjectIdentity
from oracle_db_migration_generator.model.snapshot import Coverage, SnapshotObject
from oracle_db_migration_generator.model.snapshot_io import load_snapshot
from oracle_db_migration_generator.oracle.collector import TargetObservation
from oracle_db_migration_generator.runtime.worker import save_observation
from tests.factories import actual


def test_capture_files_are_written_in_parallel_and_roundtrip(tmp_path, monkeypatch):
    snapshot = actual()
    objects, evidence = [], list(snapshot.evidence)
    for i in range(80):
        identity = ObjectIdentity(snapshot.profile_id, Identifier.parse('APP'), 'TABLE', Identifier.parse(f'T{i}'))
        raw = f'CREATE TABLE APP.T{i}(ID NUMBER);'.encode()
        sha = hashlib.sha256(raw).hexdigest()
        ev = Evidence('ev-ddl-'+str(i), 'TARGET_METADATA', 'TARGET', 'target-ddl/'+identity.key+'.sql',
                      sha, 1, 1, 'dbms_metadata.get_ddl', 'Sentetik DDL.', 0, len(raw))
        evidence.append(ev)
        objects.append(SnapshotObject(identity, {}, ev.path, sha,
            Coverage('COMPLETE', 'PARTIAL', 'COMPLETE', ('SYNTHETIC_UNPARSED',)), (ev.id,), raw))
    snapshot = replace(snapshot, objects=tuple(objects), evidence=tuple(evidence),
                       completeness=replace(snapshot.completeness, ddl='PARTIAL'))
    real = Path.write_bytes
    threads = set()
    lock = threading.Lock()
    barrier = threading.Barrier(4, timeout=4)
    def write(path, raw):
        if path.parent.name == 'target-ddl':
            with lock:
                first = threading.get_ident() not in threads
                threads.add(threading.get_ident())
            if first: barrier.wait()
        return real(path, raw)
    monkeypatch.setattr(Path, 'write_bytes', write)
    monkeypatch.setenv('GENERATOR_CAPTURE_WRITERS', '4')
    root = tmp_path/'capture'
    save_observation(TargetObservation(snapshot, {'status':'CAPTURED'}), root)
    assert len(threads) == 4
    loaded = load_snapshot(root/'target-snapshot.json')
    assert loaded.to_dict() == snapshot.to_dict()
    assert [(o.object_key, o.raw_ddl) for o in loaded.objects] == [(o.object_key, o.raw_ddl) for o in snapshot.objects]
