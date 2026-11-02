"""Taşınabilir derleyici kanıtı isteğinin kaynak kapsamını denetler.

Bu testler sentetik snapshot kullanır ve Oracle bağlantısı açmaz.

Author: Mehmet KARACAN
Date: 2026-11-01
"""

import hashlib

from oracle_db_migration_generator.portable import builder
from oracle_db_migration_generator.portable import stream
from oracle_db_migration_generator.portable import routine_capture
from oracle_db_migration_generator.model.snapshot_io import load_snapshot
from oracle_db_migration_generator.cli import main
from oracle_db_migration_generator.oracle.sequence_proof import sequence_definition, sequence_advance_matches
from oracle_db_migration_generator.oracle.routine_metadata import attach_routine_metadata
from oracle_db_migration_generator.compare.snapshots import compare_snapshots
from oracle_db_migration_generator.planning.rules import PlanningContext, plan_target
from test_compiled_routine_proof import attach, fixture, record
from test_portable_stream import encoded, packet
from tests.factories import profile
import pytest


def test_routine_capture_request_includes_source_unit_and_dependency():
    desired, target, records = fixture()
    records[0]["selected_units"] = (("PROCEDURE", "P"),)
    desired = attach(desired, records[0])

    request = builder.routine_capture_request(desired, target)

    assert request.selected_units == (("PROCEDURE", "P"),)
    assert ("APP", "P", "PROCEDURE") in request.record_keys
    assert ("APP", "T", "TABLE") in request.record_keys
    assert request.target_snapshot_digest == target.semantic_digest
    assert ("identity", None, "identity") in request.queries
    assert ("object", ("APP", "P", "PROCEDURE"), "before") in request.queries
    assert ("dependencies", ("APP", "P", "PROCEDURE"), "dependencies_after") in request.queries
    assert ("columns", ("APP", "T", "TABLE"), "columns") in request.queries


def test_routine_capture_request_keeps_external_dependencies():
    desired, target, records = fixture()
    records[0]["selected_units"] = (("PROCEDURE", "P"),)
    records[0]["records"].append(record("OTHER", "REFERENCE", "TABLE", "0" * 64))
    desired = attach(desired, records[0])

    request = builder.routine_capture_request(desired, target)

    assert ("OTHER", "REFERENCE", "TABLE") in request.record_keys


def test_verified_routine_packet_restores_ready_decision_without_oracle_access():
    desired, target, records = fixture()
    records[0]["selected_units"] = (("PROCEDURE", "P"),)
    desired = attach(desired, records[0])
    request = builder.routine_capture_request(desired, target)
    target_records = {(r["owner"], r["name"], r["kind"]): r for r in records[1]["records"]}
    rows = []
    for index, (query, key, field) in enumerate(request.queries):
        if key is None:
            result = records[1][field]
        elif field == "ddl":
            obj = next((o for o in target.objects if o.identity.name.effective_name == key[1]), None)
            result = {"state": "KNOWN", "rows": [[obj.raw_ddl.decode()]]} if obj else {"state": "KNOWN", "rows": []}
        else:
            result = target_records[key].get(field, {"state": "KNOWN", "rows": []})
        rows.append({"kind": "query", "index": index, "state": result["state"],
                     "rows": [[encoded(v) for v in row] for row in result.get("rows", [])]})
    messages = [{"kind": "header", "schema_version": "routine-capture/1.0",
                 "request_sha256": request.sha256, "session_user": "APP",
                 "database_version": "19.0.0.0.0", "captured_at": "2026-11-01T12:00:00Z"},
                *rows, {"kind": "footer", "queries": len(rows)}]

    supplement = stream.read_routine_capture(packet(messages), request, target)
    augmented, _, _ = attach_routine_metadata(target, supplement)
    p = profile()
    result = plan_target(compare_snapshots(desired, augmented, p.policy),
                         PlanningContext(desired, augmented, p, "Target"))
    unit = next(o for o in result.operations if o.identity.name.effective_name == "P")
    assert unit.decision == "READY"
    assert unit.intent.statement.startswith(b"CREATE OR REPLACE PROCEDURE APP.P")


def test_routine_script_uses_only_fixed_metadata_queries_and_bound_names():
    desired, target, records = fixture()
    records[0]["selected_units"] = (("PROCEDURE", "P"),)
    desired = attach(desired, records[0])
    request = builder.routine_capture_request(desired, target)

    script = builder.routine_capture_script(request)

    assert "DBMS_SQL.BIND_VARIABLE(v_cursor,':name',p_name)" in script
    assert "SET TRANSACTION READ ONLY" in script
    assert "CREATE PROCEDURE APP.P IS N NUMBER" not in script
    assert script.count("capture_query(") == len(request.queries) + 1


def test_routine_capture_package_is_local_and_does_not_replace_existing_files(tmp_path):
    desired, target, records = fixture()
    records[0]["selected_units"] = (("PROCEDURE", "P"),)
    desired = attach(desired, records[0])
    output = tmp_path / "routine"

    folder = builder.prepare_routine_capture(output, desired, target)

    script = (folder / "run_routine.sql").read_text(encoding="utf-8")
    assert "SPOOL routine.odmg.jsonl" in script
    assert "SET TRANSACTION READ ONLY" in script
    assert (folder / "request.json").is_file()
    with pytest.raises(ValueError, match="CAPTURE_OUTPUT_ALREADY_EXISTS"):
        builder.prepare_routine_capture(output, desired, target)


def test_missing_target_object_does_not_gain_a_false_ddl_error():
    desired, target, records = fixture()
    records[0]["selected_units"] = (("PROCEDURE", "P"),)
    desired = attach(desired, records[0])
    request = builder.routine_capture_request(desired, target)
    target_records = {(r["owner"], r["name"], r["kind"]): r for r in records[1]["records"]}
    rows = []
    for index, (query, key, field) in enumerate(request.queries):
        if field == "ddl" and key == ("APP", "P", "PROCEDURE"):
            rows.append({"kind": "query", "index": index, "state": "UNKNOWN",
                         "rows": [], "error_code": "ORA-31603"})
        else:
            result = (records[1][field] if key is None else
                      target_records[key].get(field, {"state": "KNOWN", "rows": []}))
            rows.append({"kind": "query", "index": index, "state": result["state"],
                         "rows": [[encoded(v) for v in row] for row in result.get("rows", [])]})
    messages = [{"kind": "header", "schema_version": "routine-capture/1.0",
                 "request_sha256": request.sha256, "session_user": "APP",
                 "database_version": "19.0.0.0.0", "captured_at": "2026-11-01T12:00:00Z"},
                *rows, {"kind": "footer", "queries": len(rows),
                        "messages": len(rows) + 2}]

    supplement = stream.read_routine_capture(packet(messages), request, target)
    unit = next(r for r in supplement["records"] if r["name"] == "P")
    assert unit["before"] == {"state": "KNOWN", "rows": []}
    assert "ddl" not in unit
    assert "dependency_ddl" not in unit


def test_imported_routine_capture_persists_bound_evidence(tmp_path, monkeypatch):
    desired, target, records = fixture()
    records[0]["selected_units"] = (("PROCEDURE", "P"),)
    desired = attach(desired, records[0])
    monkeypatch.setattr(routine_capture, "read_routine_capture",
                        lambda data, request, snapshot: {**records[1],
                                                         "query_count": len(request.queries)})

    output = routine_capture.import_routine_capture(
        desired, target, b"verified packet", tmp_path / "observation")

    loaded = load_snapshot(output / "target-snapshot.json", require_ddl=True)
    proof = loaded.capabilities["routine_metadata"]
    evidence = next(e for e in loaded.evidence if e.id == proof.evidence_ids[0])
    assert (output / evidence.path).is_file()
    assert evidence.sha256 == hashlib.sha256((output / evidence.path).read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="CAPTURE_OUTPUT_ALREADY_EXISTS"):
        routine_capture.import_routine_capture(desired, target, b"verified packet", output)


def test_cli_prepares_portable_routine_package(tmp_path, monkeypatch):
    desired, target, records = fixture()
    records[0]["selected_units"] = (("PROCEDURE", "P"),)
    desired = attach(desired, records[0])
    monkeypatch.setattr("oracle_db_migration_generator.model.snapshot_io.load_snapshot",
                        lambda path, **kwargs: desired if "source" in str(path) else target)
    output = tmp_path / "package"

    result = main(["prepare-routine-capture", "--source-snapshot", "source.json",
                   "--target-snapshot", "target.json", "--output", str(output)])

    assert result == 0
    assert (output / "run_routine.sql").is_file()


@pytest.mark.parametrize(("current", "accepted"), [
    ("START WITH 120 CACHE 20 NOCYCLE", True),
    ("START WITH 100 CACHE 20 NOCYCLE", True),
    ("START WITH 90 CACHE 20 NOCYCLE", False),
    ("START WITH 120 CACHE 50 NOCYCLE", False),
    ("START WITH 120 CACHE 20 CYCLE", False),
])
def test_sequence_dependency_accepts_only_forward_counter_change(current, accepted):
    old = b'CREATE SEQUENCE APP.S INCREMENT BY 1 START WITH 100 CACHE 20 NOCYCLE'
    new = ('CREATE SEQUENCE APP.S INCREMENT BY 1 ' + current).encode()
    declaration = sequence_definition(new)

    assert sequence_advance_matches(old, declaration) is accepted


def test_sequence_name_cannot_fake_noncycling_clause():
    raw = b'CREATE SEQUENCE APP."NOCYCLE" INCREMENT BY 1 START WITH 120 CACHE 20 CYCLE'

    assert sequence_definition(raw) is None
