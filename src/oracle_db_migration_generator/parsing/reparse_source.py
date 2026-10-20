"""Derive a narrow offline parser repair without replacing captured source facts."""
import hashlib
import json
from dataclasses import replace
from collections import Counter

from ..model.evidence import Evidence
from ..model.serialization import digest, thaw
from ..model.snapshot import KnownValue
from .adapter import parse_ddl
from .fingerprint import parser_artifact_sha256
from .table_logging import table_projection_input
from .canonicalize import canonical_sql


def _checked_blob(evidence, read_blob, cache):
    path = evidence.path
    if (not isinstance(path, str) or '\\' in path or ':' in path
            or any(part in {'', '.', '..'} for part in path.split('/'))):
        raise ValueError('SOURCE_REPARSE_PATH_UNSAFE')
    if path not in cache:
        cache[path] = read_blob(path)
    raw = cache[path]
    if not isinstance(raw, bytes) or hashlib.sha256(raw).hexdigest() != evidence.sha256:
        raise ValueError('SOURCE_REPARSE_BLOB_HASH_MISMATCH')
    return raw


def _span(evidence, read_blob, cache):
    raw = _checked_blob(evidence, read_blob, cache)
    start, end = evidence.start_byte, evidence.end_byte
    if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(raw)):
        raise ValueError('SOURCE_REPARSE_SPAN_UNVERIFIED')
    return raw[start:end]


def _restore_reconciled(current, original, source, evidence, read_blob, cache):
    data = json.loads(_checked_blob(evidence, read_blob, cache).decode('utf-8'))
    matches = [row for row in data.get('tables', ()) if row.get('object_key') == original.object_key
               and row.get('ddl_sha256') == original.ddl_sha256]
    if (data.get('owner') != original.identity.owner.effective_name
            or data.get('source_commit') != source.source_commit or len(matches) != 1):
        raise ValueError('SOURCE_REPARSE_RECONCILIATION_UNVERIFIED')
    old = original.properties.get('projection')
    if old is None or old.state != 'KNOWN':
        raise ValueError('SOURCE_REPARSE_RECONCILIATION_UNVERIFIED')
    props = thaw(current.properties['projection'].value)
    for name, changes in matches[0].get('resolved', {}).items():
        column = props['columns'].get(name)
        previous = old.value.get('columns', {}).get(name)
        if column is None or previous is None:
            raise ValueError('SOURCE_REPARSE_RECONCILIATION_UNVERIFIED')
        for field, value in changes.items():
            if (field not in {'length_semantics', 'collation'} or previous.get(field) != value
                    or column.get(field) not in {None, value}):
                raise ValueError('SOURCE_REPARSE_RECONCILIATION_UNVERIFIED')
            column[field] = value
    projection = replace(current.projection, properties=props)
    return replace(current, projection=projection, properties={**current.properties,
        'projection': KnownValue('KNOWN', props, current.evidence_ids)})


def _check_preserved_projection(original, updated, create_columns, *, repaired_constraints=False):
    previous = original.properties.get('projection')
    if previous is None or previous.state != 'KNOWN':
        return
    old, new = thaw(previous.value), thaw(updated.properties['projection'].value)
    phantom = old.get('columns', {}).get('SUPPLEMENTAL')
    if phantom:
        definition = phantom.get('definition', '').upper()
        if not (definition.startswith('SUPPLEMENTAL LOG ') or phantom.get('data_type', '').upper() == 'LOG'):
            raise ValueError('SOURCE_REPARSE_KNOWN_FACT_DRIFT')
        old['columns'].pop('SUPPLEMENTAL')
    # ADD COLUMN positions were previously shifted by the phantom column.
    # The verified ALTER replay establishes their correct final position.
    for name in set(old.get('columns', {})) - create_columns:
        if name in new.get('columns', {}):
            old['columns'][name]['position'] = new['columns'][name].get('position')
    for props in (old, new):
        props.pop('_generator_supplemental_logging', None)
        props.get('table_properties', {}).pop('supplemental_logging', None)
    if repaired_constraints:
        old_constraints = old.pop('constraints', {})
        new_constraints = new.pop('constraints', {})
        old_anonymous = Counter(canonical_sql(value) for key, value in old_constraints.items() if key.startswith('@anonymous-'))
        new_anonymous = Counter(canonical_sql(value) for key, value in new_constraints.items() if key.startswith('@anonymous-'))
        if (old_anonymous - new_anonymous or any(key not in new_constraints or
                canonical_sql(value) != canonical_sql(new_constraints[key])
                for key, value in old_constraints.items() if not key.startswith('@anonymous-'))):
            raise ValueError('SOURCE_REPARSE_KNOWN_CONSTRAINT_DRIFT')
    if old != new:
        raise ValueError('SOURCE_REPARSE_KNOWN_FACT_DRIFT')


def _check_file_context(original, create_proof, applied, read_blob, cache):
    """A lost ALTER evidence row cannot turn an unknown old projection into base CREATE."""
    from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens
    from .statements import qualified_parts
    raw = _checked_blob(create_proof, read_blob, cache)
    parsed = parse_ddl(raw, original.identity)
    if parsed.coverage != 'COMPLETE':
        raise ValueError('SOURCE_REPARSE_ORIGINAL_FILE_INCOMPLETE')
    for statement in parsed.sidecars:
        if statement['kind'] != 'ALTER_TABLE':
            continue
        tokens = code_tokens(statement['text'])
        boundary = 5 if len(tokens) > 3 and tokens[3].text == '.' else 3
        parts = qualified_parts(tokens[2:boundary])
        owner = parts[0] if len(parts) == 2 else original.identity.owner.effective_name
        if owner == original.identity.owner.effective_name and parts[-1] == original.identity.name.effective_name:
            if statement['text'].encode('utf-8') not in applied:
                raise ValueError('SOURCE_REPARSE_CONTEXT_EVIDENCE_MISSING')


def _reparse_object(original, source, registry, read_blob, cache, *, explicitly_selected=False):
    if not original.raw_ddl or hashlib.sha256(original.raw_ddl).hexdigest() != original.ddl_sha256:
        raise ValueError('SOURCE_REPARSE_CREATE_HASH_UNVERIFIED')
    allowed = {'DUPLICATE_COLUMN', 'PARSER_NOT_VERIFIED', 'PARSER_SYNTAX_ERROR'}
    if explicitly_selected:
        allowed.update({'CONTEXT_UNRESOLVED', 'UNNAMED_CONSTRAINT_UNRESOLVED'})
    if set(original.coverage.diagnostics) - allowed:
        raise ValueError('SOURCE_REPARSE_OTHER_DIAGNOSTIC_REMAINS')
    parsed = parse_ddl(original.raw_ddl, original.identity)
    if parsed.coverage != 'COMPLETE' or len(parsed.objects) != 1 or parsed.sidecars:
        raise ValueError('SOURCE_REPARSE_PARSE_INCOMPLETE')
    item = parsed.objects[0]
    if (item.identity != original.identity or not item.parse_ok or item.diagnostics
            or item.raw_ddl != original.raw_ddl):
        raise ValueError('SOURCE_REPARSE_IDENTITY_OR_SPAN_MISMATCH')
    props = {**original.properties, 'projection': KnownValue('KNOWN', thaw(item.projection.properties), original.evidence_ids)}
    current = replace(original, properties=props, projection=item.projection,
                      coverage=replace(original.coverage, ddl='COMPLETE', diagnostics=()))
    create_columns = set(item.projection.properties.get('columns', {}))
    create_proof = None
    reconciliations = []
    applied = set()
    from ..source.sidecars import _merge_context
    for evidence_id in original.evidence_ids:
        evidence = registry.get(evidence_id)
        if evidence is None:
            raise ValueError('SOURCE_REPARSE_EVIDENCE_MISSING')
        if evidence.kind != 'SOURCE_SPAN':
            continue
        if evidence.side != 'SOURCE':
            raise ValueError('SOURCE_REPARSE_EVIDENCE_SIDE_MISMATCH')
        if evidence.query_id == 'SOURCE_COLUMNS_KNOWN_FACTS_MATCH':
            reconciliations.append(evidence)
            continue
        if evidence.query_id == 'OFFLINE_SOURCE_SUPPLEMENTAL_REPARSE':
            continue
        span = _span(evidence, read_blob, cache)
        if span == original.raw_ddl:
            create_proof = evidence
            continue
        context = parse_ddl(span, original.identity)
        if (context.coverage != 'COMPLETE' or context.objects or len(context.sidecars) != 1
                or context.sidecars[0]['kind'] != 'ALTER_TABLE'):
            raise ValueError('SOURCE_REPARSE_CONTEXT_UNVERIFIED')
        objects = {current.object_key: current}
        _merge_context(objects, context.sidecars[0], evidence_id, original.identity.owner.effective_name)
        current = objects[current.object_key]
        applied.add(context.sidecars[0]['text'].encode('utf-8'))
    if create_proof is None:
        raise ValueError('SOURCE_REPARSE_CREATE_PROOF_MISSING')
    _check_file_context(original, create_proof, applied, read_blob, cache)
    for evidence in reconciliations:
        current = _restore_reconciled(current, original, source, evidence, read_blob, cache)
    _check_preserved_projection(original, current, create_columns,
        repaired_constraints=explicitly_selected and 'UNNAMED_CONSTRAINT_UNRESOLVED' in original.coverage.diagnostics)
    fixed = thaw(current.properties['projection'].value)
    proof = Evidence('ev-' + digest(['source-supplemental-reparse/1.0', original.object_key,
                                   original.ddl_sha256, digest(fixed), parser_artifact_sha256()]),
        'SOURCE_SPAN', 'SOURCE', create_proof.path, create_proof.sha256,
        create_proof.start_line, create_proof.end_line, 'OFFLINE_SOURCE_SUPPLEMENTAL_REPARSE',
        'Sabit kaynak DDL ve doğrulanmış ALTER/kolon kanıtları çevrimdışı yeniden ayrıştırıldı; Oracle SQL yürütülmedi.',
        create_proof.start_byte, create_proof.end_byte)
    ids = tuple(dict.fromkeys((*original.evidence_ids, proof.id)))
    return replace(current, evidence_ids=ids, properties={**current.properties,
        'projection': KnownValue('KNOWN', fixed, ids)}), proof


def reparse_source_supplemental(source, *, read_blob, object_keys=None):
    """Return a derived source and per-object audit; read_blob supplies frozen bytes.

    The default selects logging TABLEs. Explicit object_keys selects only those
    TABLE identities, including repaired context/anonymous-constraint cases.
    An empty explicit selection does nothing. Other object kinds are rejected.
    Global inventory/DDL coverage and capabilities are never upgraded. Missing
    capture/context proof leaves an explicit hold, including old COMPLETE tables.
    """
    if source.side != 'SOURCE':
        raise ValueError('SOURCE_REPARSE_REQUIRES_SOURCE')
    selected_keys = set(object_keys) if object_keys is not None else set()
    table_keys = {obj.object_key for obj in source.objects if obj.identity.object_type == 'TABLE'}
    if not selected_keys <= table_keys:
        raise ValueError('SOURCE_REPARSE_TABLE_SELECTION_INVALID')
    registry = {ev.id: ev for ev in source.evidence}
    objects, evidence, records, cache = [], list(source.evidence), [], {}
    for original in source.objects:
        selected = original.object_key in selected_keys
        if object_keys is None and original.identity.object_type == 'TABLE' and original.raw_ddl:
            try:
                _, logging = table_projection_input(original.raw_ddl.decode('utf-8'))
                selected = bool(logging)
            except (ValueError, UnicodeError, IndexError):
                pass
        if not selected:
            objects.append(original)
            continue
        try:
            updated, proof = _reparse_object(original, source, registry, read_blob, cache,
                                            explicitly_selected=original.object_key in selected_keys)
            objects.append(updated)
            if proof.id not in registry:
                evidence.append(proof)
                registry[proof.id] = proof
            records.append({'object_key': original.object_key, 'name': original.identity.name.effective_name,
                            'status': 'UPDATED', 'ddl_sha256': original.ddl_sha256, 'evidence_id': proof.id})
        except (ValueError, KeyError, TypeError, OSError, UnicodeError) as error:
            objects.append(replace(original, coverage=replace(original.coverage, ddl='PARTIAL',
                diagnostics=tuple(sorted(set((*original.coverage.diagnostics, 'SOURCE_REPARSE_PROVENANCE_UNVERIFIED')))))))
            records.append({'object_key': original.object_key, 'name': original.identity.name.effective_name,
                            'status': 'HELD', 'reason_code': str(error) if isinstance(error, ValueError) else
                            'SOURCE_REPARSE_PROVENANCE_UNVERIFIED'})
    held = sum(row['status'] == 'HELD' for row in records)
    coverage = source.completeness
    if held and coverage.ddl == 'COMPLETE':
        coverage = replace(coverage, ddl='PARTIAL', diagnostics=tuple(sorted(set(
            (*coverage.diagnostics, 'SOURCE_REPARSE_PROVENANCE_UNVERIFIED')))))
    return replace(source, objects=tuple(objects), evidence=tuple(evidence), completeness=coverage), {
        'selected': len(records), 'updated': len(records)-held, 'held': held, 'objects': records,
        'read_only': True, 'database_connections': 0, 'sql_executed': False}
