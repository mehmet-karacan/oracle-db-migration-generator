"""Derive owner inventory completeness only from closed, attributable evidence.

The captured snapshot remains immutable. Diagnostic paths establish ownership;
ordinary dependency edges never expand the selected owner set.
"""
import re
from collections.abc import Mapping
from dataclasses import replace

from ..artifacts.layout import component
from .evidence import Evidence
from .identity import Identifier
from .serialization import digest
from .snapshot import Coverage, KnownValue, SchemaSnapshot


_UNSCOPABLE = frozenset({'SOURCE_SCOPE_EMPTY', 'SOURCE_SCOPE_MISSING', 'SOURCE_OWNER_MISMATCH',
                         'SOURCE_OBJECT_TYPE_OUTSIDE_PROFILE', 'SOURCE_DEPENDENCIES_UNRESOLVED',
                         'SOURCE_DEPENDENCIES_CONFLICT'})


def _safe_path(path):
    return (isinstance(path, str) and bool(path) and '\\' not in path and ':' not in path
            and all(part not in {'', '.', '..'} for part in path.split('/')))


def _sha256(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def source_for_schemas(source: SchemaSnapshot, profile, schemas) -> SchemaSnapshot:
    """Return a derived owner view, retaining PARTIAL whenever proof is insufficient.

    ``schemas`` uses Oracle identifier spelling (quote mixed-case owners). The
    profile and its policy are unchanged. ``owner_scope_proof`` links the view to
    its original snapshot, commit, input digest, roots and validation outcome.
    """
    if source.side != 'SOURCE':
        raise ValueError('SOURCE_SCOPE_REQUIRES_SOURCE')
    selected = tuple(sorted({Identifier.parse(value).effective_name for value in schemas}))
    if not selected or not set(selected).issubset(source.schemas):
        raise ValueError('SOURCE_SCOPE_SCHEMA_OUTSIDE_SNAPSHOT')
    reasons, roots, owner_errors = set(), {}, {}
    registry = {ev.id: ev for ev in source.evidence}
    if len(registry) != len(source.evidence):
        reasons.add('SOURCE_SCOPE_DUPLICATE_EVIDENCE')
    for root in profile.schema_roots:
        owner = Identifier.parse(root.source_schema).effective_name
        if not _safe_path(root.path) or root.path in roots or owner in roots.values():
            reasons.add('SOURCE_SCOPE_ROOTS_AMBIGUOUS')
        roots[root.path] = owner
    paths = sorted(roots)
    if any(right.startswith(left + '/') for left in paths for right in paths if left != right):
        reasons.add('SOURCE_SCOPE_ROOTS_AMBIGUOUS')
    if (source.profile_id != profile.id or len(source.schemas) != len(set(source.schemas))
            or set(roots.values()) != set(source.schemas)):
        reasons.add('SOURCE_SCOPE_PROFILE_OWNERS_MISMATCH')

    def path_owner(path):
        if not _safe_path(path):
            return None
        matches = [owner for root, owner in roots.items() if path.startswith(root + '/')]
        return matches[0] if len(matches) == 1 else None

    def valid_ids(ids):
        return bool(ids) and all(ev_id in registry for ev_id in ids)

    def valid_owner_evidence(ev, owner):
        if ev.side != 'SOURCE' or not _sha256(ev.sha256):
            return False
        if ev.query_id == 'SOURCE_COLUMNS_KNOWN_FACTS_MATCH':
            suffix = '.' + component(owner) if len(source.schemas) > 1 else ''
            expected = 'metadata/source-column-semantics' + suffix + '.json'
            return ev.kind == 'SOURCE_SPAN' and ev.path == expected
        return path_owner(ev.path) == owner

    def capability(name):
        value = source.capabilities.get(name)
        if value is None or value.state != 'KNOWN' or not valid_ids(value.evidence_ids):
            reasons.add('SOURCE_SCOPE_' + name.upper() + '_UNVERIFIED')
            return None
        return value

    fingerprint = capability('source_profile_sha256')
    inputs = capability('source_input_digest')
    expected_profile_hash = digest(profile)
    if (fingerprint is None or fingerprint.value != expected_profile_hash
            or not any(registry[ev_id].kind == 'POLICY' and registry[ev_id].side == 'POLICY'
                       and registry[ev_id].sha256 == expected_profile_hash for ev_id in fingerprint.evidence_ids)):
        reasons.add('SOURCE_SCOPE_PROFILE_FINGERPRINT_UNVERIFIED')
    if (inputs is None or not _sha256(inputs.value)
            or not any(registry[ev_id].kind == 'ABSENCE_SCOPE' and registry[ev_id].side == 'SOURCE'
                       and registry[ev_id].sha256 == inputs.value for ev_id in inputs.evidence_ids)):
        reasons.add('SOURCE_SCOPE_INPUT_UNVERIFIED')

    explained, records, object_paths = set(), [], {obj.ddl_path for obj in source.objects}
    by_key = {obj.object_key: obj for obj in source.objects}
    for obj in source.objects:
        owner = obj.identity.owner.effective_name
        if (obj.identity.profile_id != source.profile_id or owner not in source.schemas
                or path_owner(obj.ddl_path) != owner):
            reasons.add('SOURCE_SCOPE_OBJECT_OWNER_PATH_MISMATCH')
        if not valid_ids(obj.evidence_ids) or not _sha256(obj.ddl_sha256):
            reasons.add('SOURCE_SCOPE_OBJECT_EVIDENCE_UNVERIFIED')
        for ev_id in obj.evidence_ids:
            ev = registry.get(ev_id)
            if ev is not None and (ev.path is not None or ev.kind == 'SOURCE_SPAN') and not valid_owner_evidence(ev, owner):
                reasons.add('SOURCE_SCOPE_OBJECT_EVIDENCE_OWNER_MISMATCH')
        if not any(registry[ev_id].path == obj.ddl_path and registry[ev_id].side == 'SOURCE'
                   and registry[ev_id].kind == 'SOURCE_SPAN' and registry[ev_id].query_id is None
                   and path_owner(registry[ev_id].path) == owner
                   and _sha256(registry[ev_id].sha256) for ev_id in obj.evidence_ids if ev_id in registry):
            reasons.add('SOURCE_SCOPE_OBJECT_PATH_UNVERIFIED')
        if any(not valid_ids(value.evidence_ids) for value in obj.properties.values()):
            reasons.add('SOURCE_SCOPE_PROPERTY_EVIDENCE_UNVERIFIED')
        for value in obj.properties.values():
            for ev_id in value.evidence_ids:
                ev = registry.get(ev_id)
                if ev is not None and (ev.path is not None or ev.kind == 'SOURCE_SPAN') and not valid_owner_evidence(ev, owner):
                    reasons.add('SOURCE_SCOPE_PROPERTY_EVIDENCE_OWNER_MISMATCH')
        if obj.identity.parent_key is not None:
            parent = by_key.get(obj.identity.parent_key)
            if parent is None or parent.identity.owner.effective_name != owner:
                reasons.add('SOURCE_SCOPE_PARENT_UNVERIFIED')
        coverage = obj.coverage
        codes = set(coverage.diagnostics)
        explained.update(codes)
        if codes & _UNSCOPABLE:
            reasons.add('SOURCE_SCOPE_UNSCOPABLE_DIAGNOSTIC')
        if coverage.inventory != 'COMPLETE' or coverage.ddl != 'COMPLETE' or codes:
            owner_errors.setdefault(owner, set()).update(codes or {'OBJECT_COVERAGE_UNVERIFIED'})
            records.append({'owner': owner, 'path': obj.ddl_path, 'codes': sorted(codes), 'kind': 'OBJECT'})
            if not codes:
                reasons.add('SOURCE_SCOPE_OBJECT_FAILURE_UNEXPLAINED')
        if any(value.state == 'UNKNOWN' for value in obj.properties.values()):
            owner_errors.setdefault(owner, set()).add('OBJECT_PROPERTY_UNKNOWN')

    files = capability('file_diagnostics')
    if files is not None and (inputs is None or any(
            registry[ev_id].kind != 'ABSENCE_SCOPE' or registry[ev_id].side != 'SOURCE'
            or registry[ev_id].sha256 != inputs.value for ev_id in files.evidence_ids)):
        reasons.add('SOURCE_SCOPE_FILE_DIAGNOSTIC_SCOPE_UNVERIFIED')
    rows = files.value if files is not None else None
    if not isinstance(rows, tuple):
        reasons.add('SOURCE_SCOPE_FILE_DIAGNOSTICS_UNVERIFIED')
        rows = ()
    for row in rows:
        if not isinstance(row, Mapping):
            reasons.add('SOURCE_SCOPE_FILE_DIAGNOSTICS_UNVERIFIED')
            continue
        owner, codes, coverage = path_owner(row.get('path')), row.get('codes'), row.get('coverage')
        if (owner is None or not isinstance(codes, tuple) or not codes
                or any(not isinstance(code, str) or not code for code in codes)
                or coverage not in {'PARTIAL', 'UNAVAILABLE'}):
            reasons.add('SOURCE_SCOPE_FILE_DIAGNOSTICS_UNVERIFIED')
            continue
        explained.update(codes)
        if row['path'] not in object_paths:
            explained.add('SOURCE_FILE_UNPARSED')
        if set(codes) & _UNSCOPABLE:
            reasons.add('SOURCE_SCOPE_UNSCOPABLE_DIAGNOSTIC')
        owner_errors.setdefault(owner, set()).update(codes)
        records.append({'owner': owner, 'path': row['path'], 'codes': list(codes), 'kind': 'FILE'})

    sidecars = source.capabilities.get('sidecar_diagnostics')
    if sidecars is not None:
        sidecars = capability('sidecar_diagnostics')
        rows = sidecars.value if sidecars is not None else None
        if not isinstance(rows, tuple):
            reasons.add('SOURCE_SCOPE_SIDECAR_DIAGNOSTICS_UNVERIFIED')
            rows = ()
        for row in rows:
            if not isinstance(row, Mapping):
                reasons.add('SOURCE_SCOPE_SIDECAR_DIAGNOSTICS_UNVERIFIED')
                continue
            owner, ev = path_owner(row.get('path')), registry.get(row.get('evidence_id'))
            if (owner is None or ev is None or ev.side != 'SOURCE' or ev.path != row.get('path')
                    or not _sha256(ev.sha256) or not isinstance(row.get('reason_code'), str)
                    or not row['reason_code'] or not isinstance(row.get('kind'), str) or not row['kind']
                    or row['evidence_id'] not in sidecars.evidence_ids):
                reasons.add('SOURCE_SCOPE_SIDECAR_DIAGNOSTICS_UNVERIFIED')
                continue
            explained.add('SOURCE_SIDECAR_UNRESOLVED')
            owner_errors.setdefault(owner, set()).add('SOURCE_SIDECAR_UNRESOLVED')
            records.append({'owner': owner, 'path': row['path'], 'codes': ['SOURCE_SIDECAR_UNRESOLVED'], 'kind': 'SIDECAR'})

    global_codes = set(source.completeness.diagnostics)
    if global_codes & _UNSCOPABLE:
        reasons.add('SOURCE_SCOPE_UNSCOPABLE_DIAGNOSTIC')
    if global_codes - explained:
        reasons.add('SOURCE_SCOPE_GLOBAL_DIAGNOSTIC_UNEXPLAINED')
    coverage = source.completeness
    if coverage.inventory not in {'COMPLETE', 'PARTIAL'} or coverage.ddl not in {'COMPLETE', 'PARTIAL'} or coverage.dictionary != 'NOT_APPLICABLE':
        reasons.add('SOURCE_SCOPE_CAPTURE_UNAVAILABLE')
    if coverage.inventory == 'PARTIAL' and 'SOURCE_FILE_UNPARSED' not in global_codes:
        reasons.add('SOURCE_SCOPE_INVENTORY_FAILURE_UNEXPLAINED')
    if coverage.ddl == 'PARTIAL' and not records:
        reasons.add('SOURCE_SCOPE_DDL_FAILURE_UNEXPLAINED')
    objects = tuple(obj for obj in source.objects if obj.identity.owner.effective_name in selected)
    if set(selected) - {obj.identity.owner.effective_name for obj in objects}:
        reasons.add('SOURCE_SCOPE_SELECTED_OWNER_EMPTY')
    if any(owner_errors.get(owner) for owner in selected):
        reasons.add('SOURCE_SCOPE_SELECTED_OWNER_PARTIAL')

    verified = not reasons
    proof = {'version': 'owner-scope/1.0', 'status': 'VERIFIED' if verified else 'UNVERIFIED',
             'raw_snapshot_digest': source.semantic_digest, 'source_commit': source.source_commit,
             'source_input_digest': inputs.value if inputs is not None else None,
             'profile_sha256': expected_profile_hash, 'schemas': list(selected),
             'roots': [{'path': path, 'owner': roots[path]} for path in sorted(roots)],
             'diagnostics': sorted(records, key=lambda row: (row['owner'], row['path'] or '', row['kind'])),
             'reasons': sorted(reasons)}
    proof_hash = digest(proof)
    evidence_id = 'ev-' + proof_hash
    evidence = Evidence(evidence_id, 'ABSENCE_SCOPE' if verified else 'POLICY', 'SOURCE' if verified else 'POLICY',
                        None, proof_hash, None, None, None,
                        'Sabit ham kaynak snapshotından seçili owner kapsamı; tamlık yalnız doğrulanmış kapsam için geçerlidir.')
    capabilities = {**source.capabilities, 'owner_scope_proof': KnownValue('KNOWN', proof, (evidence_id,))}
    completeness = (Coverage('COMPLETE', 'COMPLETE', coverage.dictionary) if verified else
                    Coverage('PARTIAL', 'PARTIAL', coverage.dictionary,
                             tuple(sorted(global_codes | {'SOURCE_OWNER_SCOPE_UNVERIFIED'}))))
    return replace(source, schemas=selected, objects=objects, completeness=completeness,
                   capabilities=capabilities, evidence=(*source.evidence, evidence))
