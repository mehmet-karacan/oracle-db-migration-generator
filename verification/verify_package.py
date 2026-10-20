"""Validate this handoff package; this is NOT a Generator implementation or Oracle test.
Run: python verification/verify_package.py
Requires jsonschema (available in the reference Analyzer environment).
"""
from __future__ import annotations
import copy, hashlib, json, re, sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]

def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()

def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:
        print("Package check needs jsonschema; no environment was modified.", file=sys.stderr)
        return 2
    schemas = {}
    for path in sorted((ROOT / "schemas").glob("*.json")):
        s = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(s)
        schemas[path.name] = Draft202012Validator(s, format_checker=FormatChecker())
    examples = [
        ("targets.example.json", "targets.schema.json"),
        ("source-profile.example.json", "source-profile.schema.json"),
        ("source-snapshot.example.json", "snapshot.schema.json"),
        ("target-snapshot.example.json", "snapshot.schema.json"),
        ("plan.example.json", "plan.schema.json"),
        ("run.example.json", "run.schema.json"),
        ("bundle-manifest.example.json", "bundle-manifest.schema.json"),
    ]
    for file, schema in examples:
        schemas[schema].validate(load("examples/" + file))
    schemas["source-profile.schema.json"].validate(load(".local/source-profile.sky.json"))
    # Negative schema cases prove closed shape and guardrails of supplied contracts.
    negative = []
    t = load("examples/targets.example.json")
    x = copy.deepcopy(t); x["targets"][0]["endpoint"]["sid"] = "WRONG_BOTH"; negative.append((x, "targets.schema.json"))
    x = copy.deepcopy(t); x["targets"][0]["password"] = "NOT_A_REAL_SECRET"; negative.append((x, "targets.schema.json"))
    x = copy.deepcopy(t); x["targets"][0]["endpoint"]["port"] = 0; negative.append((x, "targets.schema.json"))
    p = load("examples/plan.example.json")
    x = copy.deepcopy(p); x["operations"][0]["decision"] = "BLOCKED"; negative.append((x, "plan.schema.json"))
    x = copy.deepcopy(p); x["operations"][0]["before"]["state"] = "UNKNOWN"; negative.append((x, "plan.schema.json"))
    for illegal in ("../outside.sql", "C:/outside.sql", "/absolute.sql"):
        x = copy.deepcopy(p); x["operations"][0]["sql"]["path"] = illegal; negative.append((x, "plan.schema.json"))
    for data, schema in negative:
        check(bool(list(schemas[schema].iter_errors(data))), "Negative example was accepted: " + schema)
    # Normative example plan-core fingerprint, no circular final-SQL hash.
    core = copy.deepcopy(p); core.pop("plan_id"); core.pop("validation")
    for op in core["operations"]:
        op["sql"] = None
    check(canonical_hash(core) == p["plan_id"], "Plan ID mismatch")
    mutated = copy.deepcopy(core); mutated["input_fingerprint"]["parser_version"] += "-changed"
    check(canonical_hash(mutated) != p["plan_id"], "Parser fingerprint not part of plan ID")
    for sf in ("source-snapshot.example.json", "target-snapshot.example.json"):
        snapshot = load("examples/" + sf); expected = snapshot.pop("semantic_digest")
        check(canonical_hash(snapshot) == expected, "Snapshot digest mismatch: " + sf)
    evidence_ids = {ev["id"] for ev in p["evidence"]}
    change_ids = {d["id"] for d in p["differences"]}
    op_ids = {op["id"] for op in p["operations"]}
    check(len(evidence_ids) == len(p["evidence"]), "Duplicate evidence ID")
    check(len(change_ids) == len(p["differences"]), "Duplicate difference ID")
    check(len(op_ids) == len(p["operations"]), "Duplicate operation ID")
    for op in p["operations"]:
        check(set(op["evidence_ids"]) <= evidence_ids, "Unresolved operation evidence")
        check(set(op["change_ids"]) <= change_ids, "Unresolved change ID")
        check(set(op["depends_on"]) <= op_ids, "Unresolved dependency")
        if op["sql"]:
            path = ROOT / "examples" / op["sql"]["path"]
            check(path.is_file() and file_hash(path) == op["sql"]["sha256"], "SQL hash mismatch")
    check(p["differences"][0]["before"]["value"] == 40, "Expected actual=40")
    check(p["differences"][0]["after"]["value"] == 80, "Expected desired=80")
    check(p["counts"]["observed_differences"] == len(p["differences"]), "Difference count mismatch")
    dc = Counter(op["decision"] for op in p["operations"])
    for k, decision in [("ready_operations", "READY"), ("review_operations", "REVIEW_REQUIRED"), ("blocked_operations", "BLOCKED")]:
        check(p["counts"][k] == dc[decision], "Decision count mismatch")
    for ev in p["evidence"]:
        if ev["path"]:
            path = ROOT / "examples" / ev["path"]
            check(file_hash(path) == ev["sha256"], "Evidence hash mismatch")
            check(1 <= ev["start_line"] <= ev["end_line"] <= len(path.read_text().splitlines()), "Evidence span out of range")
    b = load("examples/bundle-manifest.example.json")
    check(b["plan_id"] == p["plan_id"], "Bundle plan mismatch")
    for entry in b["files"]:
        path = ROOT / "examples" / entry["path"]
        check(path.is_file() and path.stat().st_size == entry["bytes"] and file_hash(path) == entry["sha256"], "Bundle file mismatch: " + entry["path"])
    # Explicit Markdown links (future implementation filenames in code spans are not links).
    link_count = 0
    for md in ROOT.rglob("*.md"):
        text = re.sub(r"```.*?```", "", md.read_text(encoding="utf-8"), flags=re.S)
        for target in re.findall(r"\[[^\]]+\]\(([^\s)]+)\)", text):
            url = urlsplit(target)
            if url.scheme or target.startswith("#"):
                continue
            resolved = (md.parent / unquote(url.path)).resolve()
            check(resolved.is_relative_to(ROOT), "Link escapes package")
            check(resolved.exists(), f"Broken Markdown link: {md.relative_to(ROOT)} -> {target}")
            link_count += 1
    for required in ("AGENTS.md", "AKTIF_GOREV.md", "reference-lock.json", "reference-ui/reference.html", "reference-ui/innova-report.original.html.j2"):
        check((ROOT / required).is_file(), "Required package file absent: " + required)
    # Design source immutability, verified against original-reference byte fingerprints.
    refs = load("reference-lock.json")
    source_refs = {p["id"]: {x["path"]: x for x in p["files"]} for p in refs["projects"]}
    for project, original, copied in [
        ("analyzer", "src/db_change_analyzer/templates/innova_v1/report_email.html.j2", "reference-ui/innova-report.original.html.j2"),
        ("analyzer", "src/db_change_analyzer/assets/innova-logo-approved.png", "reference-ui/innova-logo-approved.png"),
        ("ddl_sync", "templates/mail_report.html", "reference-ui/ddl-sync-report.secondary.html.j2"),
    ]:
        check(file_hash(ROOT / copied) == source_refs[project][original]["sha256"], "Reference copy differs: " + copied)
    for path in ROOT.rglob("*"):
        check(path.suffix.lower() not in {".ttf", ".otf", ".woff", ".woff2"}, "Font file must not be included")
    mf = ROOT / "PACKAGE_MANIFEST.json"
    manifest_verified = False
    if mf.exists():
        manifest = load("PACKAGE_MANIFEST.json")
        expected_paths = {f["path"] for f in manifest["files"]}
        actual_paths = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p != mf and "__pycache__" not in p.parts}
        check(expected_paths == actual_paths, "Package file inventory mismatch")
        for rec in manifest["files"]:
            path = ROOT / rec["path"]
            check(file_hash(path) == rec["sha256"] and path.stat().st_size == rec["bytes"], "Package integrity mismatch: " + rec["path"])
        manifest_verified = True
    print(json.dumps({"status": "PASS", "scope": "handoff package only", "schemas": len(schemas), "positive_json_instances": len(examples)+1, "negative_schema_cases": len(negative), "markdown_links": link_count, "example_plan_integrity": "PASS", "reference_asset_hashes": "PASS", "package_manifest_verified": manifest_verified, "generator_implementation_tests": "NOT_RUN", "live_oracle_jenkins": "NOT_RUN"}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
