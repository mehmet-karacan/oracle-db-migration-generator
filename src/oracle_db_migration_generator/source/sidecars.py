"""Merge comments/grants/dependencies with explicit identities and evidence."""
import hashlib
import json
import re
from dataclasses import replace

from ..model.evidence import Evidence
from ..model.identity import Identifier, ObjectIdentity
from ..model.serialization import digest, thaw
from ..model.snapshot import Coverage, KnownValue, SnapshotObject
from ..parsing.canonicalize import canonical_sql
from ..parsing.projections import normalize_projection
from ..parsing.statements import sidecar_facts
from .._vendor.analyzer_core.oracle.projections import project
from .._vendor.analyzer_core.oracle.scanner import scan


def merge_sidecars(snapshot, sidecars, *, parsed_results=None):
    from ..parsing.adapter import parse_ddl
    parsed_results = parsed_results or {}
    objects = {obj.object_key: obj for obj in snapshot.objects}
    evidence = list(snapshot.evidence)
    diagnostics = list(snapshot.completeness.diagnostics)
    initial_diagnostic_count = len(diagnostics)
    failures=[]
    for artifact in sidecars:
        if artifact.kind == 'MANIFEST':
            continue
        if artifact.kind == 'DEPENDENCIES':
            try:
                data = json.loads(artifact.raw.decode('utf-8-sig'))
                owner, name, kind = data['schema'], data['object']['name'], data['object']['type'].replace(' ', '_')
                if owner!=Identifier.parse(artifact.source_schema).effective_name:
                    raise ValueError('DEPENDENCY_OWNER_MISMATCH')
                paired_kind={'PACKAGE':'PACKAGE_BODY','TYPE':'TYPE_BODY'}.get(kind)
                kind = {'PACKAGE':'PACKAGE_SPEC', 'TYPE':'TYPE_SPEC'}.get(kind, kind)
                candidate = next((obj for obj in objects.values() if obj.identity.owner.effective_name == owner
                                  and obj.identity.name.effective_name == name and obj.identity.object_type == kind), None)
                if candidate is None:
                    raise ValueError('DEPENDENCY_PARENT_NOT_FOUND')
                refs = data['depends_on']
                if not isinstance(refs, list) or any(not isinstance(ref, dict) or not all(isinstance(ref.get(k), str) for k in ('owner','type','name')) for ref in refs):
                    raise ValueError('DEPENDENCY_SCHEMA_INVALID')
                ev_id = 'ev-' + digest([artifact.path, artifact.sha256, 'dependencies'])
                evidence.append(Evidence(ev_id, 'DEPENDENCY', snapshot.side, artifact.path, artifact.sha256,
                                         None, None, None, 'Kaynak bağımlılık sidecar kaydı.'))
                # Sync layout._deps_for emits the union of spec/body edges for
                # PACKAGE/TYPE. A BODY-specific inventory stays BODY-specific.
                candidates=[candidate]
                if paired_kind:
                    candidates.extend(obj for obj in objects.values() if obj.identity.owner.effective_name==owner
                                      and obj.identity.name.effective_name==name and obj.identity.object_type==paired_kind)
                values=sorted(refs,key=lambda ref:(ref['owner'],ref['type'],ref['name']))
                conflicts=[item for item in candidates if (previous:=item.properties.get('dependencies')) is not None
                           and (previous.state!='KNOWN' or thaw(previous.value)!=values)]
                if conflicts:
                    for item in conflicts:
                        ids=tuple(dict.fromkeys((*item.evidence_ids,ev_id)))
                        objects[item.object_key]=replace(item,properties={**item.properties,'dependencies':KnownValue('UNKNOWN',None,ids)},
                            evidence_ids=ids,coverage=replace(item.coverage,ddl='PARTIAL',
                                diagnostics=tuple(sorted(set((*item.coverage.diagnostics,'SOURCE_DEPENDENCIES_CONFLICT'))))))
                    raise ValueError('SOURCE_DEPENDENCIES_CONFLICT')
                for item in candidates:
                    props = dict(item.properties)
                    props['dependencies'] = KnownValue('KNOWN', values, (ev_id,))
                    props['used_by'] = KnownValue('KNOWN', data.get('used_by', []), (ev_id,))
                    objects[item.object_key] = replace(item, properties=props,evidence_ids=tuple(dict.fromkeys((*item.evidence_ids,ev_id))))
            except (ValueError, TypeError, KeyError, UnicodeError):
                diagnostics.append('SOURCE_DEPENDENCIES_UNRESOLVED')
            continue
        result = parsed_results.get(artifact.path)
        if result is None:
            hint = ObjectIdentity(snapshot.profile_id, Identifier.parse(artifact.source_schema),
                                  artifact.object_type_hint or 'TABLE', Identifier.parse('UNRESOLVED'))
            result = parse_ddl(artifact.raw, hint)
        for statement in result.sidecars:
            ev_id = 'ev-' + digest([artifact.path, artifact.sha256, statement['start_char'], statement['end_char'], statement['kind']])
            text = artifact.raw.decode('utf-8')
            start, end = statement['start_char'], statement['end_char']
            start_byte, end_byte = len(text[:start].encode()), len(text[:end].encode())
            evidence.append(Evidence(ev_id, 'SOURCE_SPAN', snapshot.side, artifact.path, artifact.sha256,
                                     text.count('\n',0,start)+1, text.count('\n',0,end)+1, None,
                                     'Kaynak sidecar statement aralığı.', start_byte, end_byte))
            try:
                facts = sidecar_facts(statement['text'], artifact.source_schema)
                if statement['kind'] in {'ALTER_TABLE', 'ALTER_TRIGGER','ALTER_INDEX'}:
                    _merge_context(objects, statement, ev_id, artifact.source_schema)
                    continue
                for fact in facts:
                    parents = [obj for obj in objects.values() if obj.identity.owner.effective_name == fact['owner']
                               and obj.identity.name.effective_name == fact['target']
                               and obj.identity.object_type not in {'COMMENT','GRANT','INDEX','TRIGGER','PACKAGE_BODY','TYPE_BODY'}]
                    parent = parents[0] if len(parents) == 1 else None
                    reasons = [] if parent else ['SIDECAR_PARENT_UNRESOLVED']
                    if fact.get('column_grant'):
                        reasons.append('COLUMN_GRANT_NOT_SUPPORTED')
                    identity_parts = [fact['kind'], fact['owner'], fact['target'], fact.get('column'),
                                      fact.get('grantee'), fact.get('privilege')]
                    identity = ObjectIdentity(snapshot.profile_id,
                                              Identifier(fact['owner'],fact['owner'],True),fact['kind'],
                                              Identifier('S_' + digest(identity_parts), 'SIDECAR', False),
                                              parent.object_key if parent else None)
                    raw = fact.pop('raw_ddl')
                    props = {key: KnownValue('KNOWN', value, (ev_id,)) for key, value in fact.items() if key != 'kind'}
                    props['definition'] = KnownValue('KNOWN',canonical_sql(raw.decode()),(ev_id,))
                    item = SnapshotObject(identity,props,artifact.path,hashlib.sha256(raw).hexdigest(),
                                          Coverage('COMPLETE','PARTIAL' if reasons else 'COMPLETE','NOT_APPLICABLE',tuple(reasons)),
                                          (ev_id,),raw,None)
                    previous = objects.get(item.object_key)
                    if previous:
                        if {k:thaw(v.value) for k,v in previous.properties.items()} != {k:thaw(v.value) for k,v in props.items()}:
                            item = replace(item, coverage=Coverage('COMPLETE','PARTIAL','NOT_APPLICABLE',('DUPLICATE_SIDECAR_CONFLICT',)))
                        item = replace(item,evidence_ids=previous.evidence_ids+(ev_id,))
                    objects[item.object_key] = item
            except (ValueError, TypeError, KeyError, StopIteration) as error:
                diagnostics.append('SOURCE_SIDECAR_UNRESOLVED')
                code=str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z][A-Z0-9_]{1,80}',str(error)) else 'SIDECAR_FACT_UNRESOLVED'
                failures.append({'path':artifact.path,'kind':statement['kind'],'reason_code':code,
                                 'start_byte':start_byte,'end_byte':end_byte,'evidence_id':ev_id})
    partial = (snapshot.completeness.ddl != 'COMPLETE' or len(diagnostics) > initial_diagnostic_count
               or any(obj.coverage.ddl != 'COMPLETE' for obj in objects.values()))
    capabilities=dict(snapshot.capabilities)
    if failures:
        capabilities['sidecar_diagnostics']=KnownValue('KNOWN',failures,tuple(item['evidence_id'] for item in failures))
    unique_evidence={}
    for item in evidence:
        if item.id in unique_evidence and unique_evidence[item.id]!=item:
            raise ValueError('EVIDENCE_ID_CONFLICT')
        unique_evidence[item.id]=item
    return replace(snapshot,objects=tuple(sorted(objects.values(),key=lambda obj:obj.object_key)),evidence=tuple(unique_evidence.values()),capabilities=capabilities,
                   completeness=replace(snapshot.completeness,ddl='PARTIAL' if partial else 'COMPLETE',
                                        diagnostics=tuple(sorted(set(diagnostics)))))


def _merge_context(objects, statement, evidence_id, default_schema):
    # Only validated ALTER statements are projected. They are never emitted as
    # source commands; the planner later derives permitted operations.
    from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens, identifier
    from ..parsing.statements import qualified_parts
    tokens = code_tokens(statement['text'])
    words = [token.upper for token in tokens]
    boundary=5 if len(tokens)>3 and tokens[3].text=='.' else 3
    parts = qualified_parts(tokens[2:boundary])
    expected_type = {'ALTER_TRIGGER':'TRIGGER','ALTER_TABLE':'TABLE','ALTER_INDEX':'INDEX'}[statement['kind']]
    owner = parts[0] if len(parts)==2 else Identifier.parse(default_schema).effective_name
    matches = [obj for obj in objects.values() if obj.identity.object_type==expected_type
               and obj.identity.name.effective_name == parts[-1]
               and obj.identity.owner.effective_name == owner]
    if len(matches) != 1:
        raise ValueError('CONTEXT_TARGET_UNRESOLVED')
    previous = matches[0]
    from ..parsing.context import apply_context
    try:
        objects[previous.object_key] = apply_context(previous,statement['text'],evidence_id,boundary)
    except (ValueError,KeyError,TypeError):
        props = dict(previous.properties)
        props['projection'] = KnownValue('UNKNOWN',None,previous.evidence_ids+(evidence_id,))
        objects[previous.object_key] = replace(previous,properties=props,
                                              coverage=replace(previous.coverage,ddl='PARTIAL',diagnostics=previous.coverage.diagnostics+('CONTEXT_UNRESOLVED',)),
                                              evidence_ids=previous.evidence_ids+(evidence_id,))
        raise
