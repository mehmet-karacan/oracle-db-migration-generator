import hashlib
from dataclasses import dataclass, replace

from ..model.evidence import Evidence
from ..model.identity import Identifier, ObjectIdentity
from ..model.serialization import digest, thaw
from ..model.snapshot import Coverage, KnownValue, SchemaSnapshot, SnapshotObject
from .canonicalize import canonical_sql
from .client import request_parse
from .codec import decode
from .projections import normalize_projection


@dataclass(frozen=True, slots=True)
class ParsedObject:
    identity: ObjectIdentity
    projection: object
    raw_ddl: bytes
    start_byte: int
    end_byte: int
    start_line: int
    end_line: int
    parse_ok: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ParseResult:
    objects: tuple[ParsedObject, ...]
    sidecars: tuple[dict, ...]
    diagnostics: tuple[str, ...]
    coverage: str

    @property
    def projections(self):
        return tuple(obj.projection for obj in self.objects)


def parse_ddl(raw: bytes, identity_hint: ObjectIdentity | None,*,metadata=False) -> ParseResult:
    owner = identity_hint.owner.effective_name if identity_hint else None
    timeout=120 if len(raw)>24*1024 else 30
    # Full-grammar frozen captures measured 157–202s for large package bodies.
    # Keep that narrow case bounded; all other unit budgets stay unchanged.
    if identity_hint and identity_hint.object_type=='PACKAGE_BODY' and len(raw)>128*1024:
        timeout=240
    try:
        payload = request_parse(raw, owner,timeout=timeout,metadata=metadata)
    except TimeoutError:
        return ParseResult((), (), ('PARSER_TIMEOUT',), 'UNAVAILABLE')
    except (RuntimeError, BrokenPipeError):
        return ParseResult((), (), ('PARSER_WORKER_TERMINATED',), 'UNAVAILABLE')
    try:
        text = raw.decode('utf-8')
    except UnicodeError:
        return ParseResult((), (), ('ENCODING_UNRESOLVED',), 'UNAVAILABLE')
    objects = []
    for data in payload['objects']:
        source_owner = data['raw_schema'] or owner
        if not source_owner:
            continue
        schema = Identifier(source_owner if data['schema_quoted'] else source_owner.upper(), source_owner, data['schema_quoted'])
        name = Identifier(data['raw_name'] if data['name_quoted'] else data['raw_name'].upper(), data['raw_name'], data['name_quoted'])
        identity = ObjectIdentity(identity_hint.profile_id if identity_hint else 'unscoped', schema, data['object_type'], name)
        start_char, end_char = data['start_char'], data['end_char']
        start, end = len(text[:start_char].encode()), len(text[:end_char].encode())
        projection = normalize_projection(decode(data['projection']),text[start_char:end_char])
        diagnostics = tuple(sorted(set(data['diagnostics'] + list(projection.diagnostics))))
        if identity_hint and schema != identity_hint.owner:
            diagnostics += ('SOURCE_OWNER_MISMATCH',)
        objects.append(ParsedObject(identity, projection, raw[start:end], start, end,
                                    text.count('\n', 0, start_char) + 1,
                                    text.count('\n', 0, end_char) + 1,
                                    data['parse_ok'], diagnostics))
    diagnostics = tuple(payload['diagnostics'])
    partial = bool(diagnostics or any(not obj.parse_ok or obj.diagnostics for obj in objects))
    return ParseResult(tuple(objects), tuple(payload['sidecars']), diagnostics, 'PARTIAL' if partial else 'COMPLETE')


def parse_source(inputs, profile, *, progress=None) -> SchemaSnapshot:
    from .inventory import inspect_artifact, fallback_objects, attach_inventory_proof
    objects, evidence, diagnostics = {}, [], []
    parsed_results = {}
    file_diagnostics = []
    inventory_records = []
    for index, artifact in enumerate(inputs.artifacts):
        if progress:
            progress(index, len(inputs.artifacts))
        if artifact.kind in {'MANIFEST', 'DEPENDENCIES'}:
            continue
        hint = ObjectIdentity(profile.id, Identifier.parse(artifact.source_schema),
                              artifact.object_type_hint or 'TABLE', Identifier.parse('UNRESOLVED'))
        result = parse_ddl(artifact.raw, hint)
        inventory = inspect_artifact(artifact, profile, result)
        inventory_records.append(inventory)
        original_missing = result.coverage != 'COMPLETE' and not result.objects
        result = fallback_objects(artifact, profile, result, inventory, ParsedObject)
        parsed_results[artifact.path] = result
        if result.diagnostics:
            file_diagnostics.append({'path':artifact.path,'codes':list(result.diagnostics),'coverage':result.coverage})
        diagnostics.extend(result.diagnostics)
        for parsed in result.objects:
            if parsed.identity.object_type not in profile.object_types:
                diagnostics.append('SOURCE_OBJECT_TYPE_OUTSIDE_PROFILE')
                continue
            evidence_id = 'ev-' + digest([artifact.path, artifact.sha256, parsed.start_byte, parsed.end_byte])
            evidence.append(Evidence(evidence_id, 'SOURCE_SPAN', 'SOURCE', artifact.path, artifact.sha256,
                                     parsed.start_line, parsed.end_line, None, 'Kaynak DDL nesne aralığı.',
                                     parsed.start_byte, parsed.end_byte))
            ids = (evidence_id,)
            known = parsed.parse_ok and not parsed.diagnostics
            properties = {'projection': KnownValue('KNOWN' if known else 'UNKNOWN',
                                                   thaw(parsed.projection.properties) if known else None, ids),
                          'definition': KnownValue('KNOWN' if parsed.parse_ok else 'UNKNOWN',
                                                   parsed.projection.properties.get('_generator_effective_definition',canonical_sql(parsed.raw_ddl.decode())) if parsed.parse_ok else None, ids)}
            obj = SnapshotObject(parsed.identity, properties, artifact.path, hashlib.sha256(parsed.raw_ddl).hexdigest(),
                                 Coverage('COMPLETE', 'COMPLETE' if known else 'PARTIAL', 'NOT_APPLICABLE', parsed.diagnostics),
                                 ids, parsed.raw_ddl, parsed.projection)
            previous = objects.get(obj.object_key)
            if previous:
                conflict = canonical_sql(previous.raw_ddl.decode()) != canonical_sql(obj.raw_ddl.decode())
                coverage = Coverage('COMPLETE', 'PARTIAL', 'NOT_APPLICABLE', ('DUPLICATE_DEFINITION_CONFLICT',)) if conflict else previous.coverage
                obj = replace(previous, evidence_ids=previous.evidence_ids + ids, coverage=coverage)
            objects[obj.object_key] = obj
        if original_missing:
            diagnostics.append('SOURCE_FILE_UNPARSED')
    if not objects:
        diagnostics.append('SOURCE_SCOPE_EMPTY')
    partial = bool(diagnostics or any(obj.coverage.ddl != 'COMPLETE' for obj in objects.values()))
    scope_id = 'ev-'+digest([inputs.revision.commit,inputs.input_digest,'source-inventory'])
    evidence.append(Evidence(scope_id,'ABSENCE_SCOPE','SOURCE',None,inputs.input_digest,None,None,None,
                             'Sabit Git SHA kapsamındaki dosyaların tam envanteri.'))
    profile_id = 'ev-'+digest(['source-profile',profile])
    evidence.append(Evidence(profile_id,'POLICY','POLICY',None,digest(profile),None,None,None,
                             'Kaynak profilinin kanonik yapılandırma özeti.'))
    capabilities = {'source_profile_sha256':KnownValue('KNOWN',digest(profile),(profile_id,)),
                    'source_input_digest':KnownValue('KNOWN',inputs.input_digest,(scope_id,)),
                    'file_diagnostics':KnownValue('KNOWN',file_diagnostics,(scope_id,)),
                    'source_length_semantics':KnownValue('UNKNOWN' if profile.source_length_semantics=='UNKNOWN' else 'KNOWN',
                                                        None if profile.source_length_semantics=='UNKNOWN' else profile.source_length_semantics,(profile_id,))}
    snapshot = SchemaSnapshot('snapshot/1.0', False, 'SOURCE', profile.id,
                              tuple(Identifier.parse(root.source_schema).effective_name for root in profile.schema_roots), inputs.revision.commit, None,
                              tuple(sorted(objects.values(), key=lambda item: item.object_key)),
                              Coverage('PARTIAL' if any(code in diagnostics for code in ('SOURCE_FILE_UNPARSED','SOURCE_SCOPE_EMPTY','SOURCE_OBJECT_TYPE_OUTSIDE_PROFILE')) else 'COMPLETE',
                                       'PARTIAL' if partial else 'COMPLETE', 'NOT_APPLICABLE', tuple(sorted(set(diagnostics)))),
                              capabilities, tuple(evidence), 'NOT_APPLICABLE')
    from ..source.sidecars import merge_sidecars
    merged = merge_sidecars(snapshot, inputs.artifacts, parsed_results=parsed_results)
    return attach_inventory_proof(merged, inputs, profile, inventory_records)
