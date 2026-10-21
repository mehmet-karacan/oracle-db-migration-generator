"""One offline interpretation of GET_DDL bytes for live and replayed captures."""
from dataclasses import replace

from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens
from ..model.evidence import Evidence
from ..model.serialization import digest,thaw
from ..model.snapshot import KnownValue
from ..parsing.adapter import parse_ddl
from ..parsing.canonicalize import canonical_sql
from ..parsing.context import apply_context


def project_target_object(obj):
    if obj.raw_ddl is None: return obj,()
    parsed=parse_ddl(obj.raw_ddl,obj.identity,metadata=True)
    candidate=next((item for item in parsed.objects if item.identity.key==obj.object_key),None)
    reasons=set(parsed.diagnostics)
    if candidate is None:
        reasons.add('TARGET_DDL_IDENTITY_UNRESOLVED')
    else:
        reasons.update(candidate.diagnostics)
        if not candidate.parse_ok: reasons.add('PARSER_NOT_VERIFIED')
    if parsed.coverage!='COMPLETE' and not reasons:
        reasons.add('PARSER_RESULT_INCOMPLETE')
    props=dict(obj.properties)
    known=candidate is not None and not reasons
    props['projection']=KnownValue('KNOWN' if known else 'UNKNOWN',thaw(candidate.projection.properties) if known else None,obj.evidence_ids)
    props['definition']=KnownValue('KNOWN' if known else 'UNKNOWN',candidate.projection.properties.get('_generator_effective_definition',canonical_sql(candidate.raw_ddl.decode())) if known else None,obj.evidence_ids)
    updated=replace(obj,properties=props,projection=candidate.projection if candidate else None,
                    coverage=replace(obj.coverage,ddl='COMPLETE' if known else 'PARTIAL',diagnostics=tuple(sorted(reasons))))
    evidence=[]
    if known:
        for statement in parsed.sidecars:
            if statement['kind'] not in {'ALTER_TABLE','ALTER_TRIGGER','ALTER_INDEX'}: continue
            text=obj.raw_ddl.decode();begin,end=statement['start_char'],statement['end_char']
            start_byte,end_byte=len(text[:begin].encode()),len(text[:end].encode())
            ev_id='ev-'+digest([obj.object_key,obj.ddl_sha256,statement['kind'],start_byte,end_byte,'target-context'])
            evidence.append(Evidence(ev_id,'TARGET_METADATA','TARGET',obj.ddl_path,obj.ddl_sha256,
                                     text.count('\n',0,begin)+1,text.count('\n',0,end)+1,'dbms_metadata.get_ddl',
                                     'Kaydedilmiş GET_DDL blobundaki context statement kanıtı.',start_byte,end_byte))
            tokens=code_tokens(statement['text']) or ()
            boundary=5 if len(tokens)>3 and tokens[3].text=='.' else 3
            try:
                updated=apply_context(updated,statement['text'],ev_id,boundary)
            except (ValueError,KeyError,TypeError):
                props=dict(updated.properties);props['projection']=KnownValue('UNKNOWN',None,updated.evidence_ids+(ev_id,))
                updated=replace(updated,properties=props,coverage=replace(updated.coverage,ddl='PARTIAL',
                                    diagnostics=updated.coverage.diagnostics+('CONTEXT_UNRESOLVED',)))
    return updated,tuple(evidence)
