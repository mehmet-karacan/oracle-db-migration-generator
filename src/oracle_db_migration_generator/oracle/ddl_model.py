"""Şema Karşılaştırma hedef DDL metnini çözümler ve aynı paket bilgisini kullanır.

Author: Mehmet KARACAN
Date: 2026-11-06
"""
from dataclasses import replace
import hashlib
from antlr4 import InputStream
from antlr4.error.ErrorListener import ErrorListener

from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens
from ..model.evidence import Evidence
from ..model.serialization import digest,thaw
from ..model.snapshot import KnownValue
from ..parsing.adapter import parse_ddl
from ..parsing.canonicalize import canonical_sql
from ..parsing.context import apply_context


class _StrictErrors(ErrorListener):
    """Paket eşitliği kontrolünde geçersiz karakterlerin atılmasını önler.

    Author: Mehmet KARACAN
    Date: 2026-11-06
    """
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise ValueError('SQL_LEXER_ERROR')


def _checked_canonical(text):
    from .._vendor.analyzer_core.oracle.generated.PlSqlLexer import PlSqlLexer
    lexer = PlSqlLexer(InputStream(text.lstrip('\ufeff')))
    lexer.removeErrorListeners()
    lexer.addErrorListener(_StrictErrors())
    protected = []
    while True:
        token = lexer.nextToken()
        if token.type == -1:
            break
        if (token.channel == 0 and "'" in token.text) or token.text.startswith(('/*+', '--+')):
            protected.append(token.text)
    return canonical_sql(text), tuple(protected)


def _matching_package(obj, source, statistics):
    """Kimliği ve içeriği eşleşen doğrulanmış paketin bilgisini hedefe taşır."""
    if (source is None or obj.identity.object_type not in {'PACKAGE_SPEC', 'PACKAGE_BODY'}
            or source.object_key != obj.object_key or not source.raw_ddl or not obj.raw_ddl
            or source.coverage.ddl != 'COMPLETE' or source.coverage.diagnostics
            or obj.coverage.diagnostics):
        return None
    projected = source.properties.get('projection')
    definition = source.properties.get('definition')
    if (not projected or projected.state != 'KNOWN' or not definition or definition.state != 'KNOWN'
            or not isinstance(definition.value, str)):
        return None
    source_hash = hashlib.sha256(source.raw_ddl).hexdigest()
    target_hash = hashlib.sha256(obj.raw_ddl).hexdigest()
    if source_hash != source.ddl_sha256 or target_hash != obj.ddl_sha256:
        return None
    exact = source_hash == target_hash and source.raw_ddl == obj.raw_ddl
    try:
        if exact:
            canonical = definition.value
        else:
            canonical, protected = _checked_canonical(obj.raw_ddl.decode('utf-8'))
            desired, source_protected = _checked_canonical(source.raw_ddl.decode('utf-8'))
            if (hashlib.sha256(canonical.encode()).digest() != hashlib.sha256(desired.encode()).digest()
                    or canonical != desired or protected != source_protected):
                return None
        from ..compare.projection_adapter import restore_projection
        projection = restore_projection(source)
        if projection is None or projection.diagnostics:
            return None
    except (ValueError, UnicodeError, KeyError, TypeError):
        return None
    props = dict(obj.properties)
    props['projection'] = KnownValue('KNOWN', thaw(projection.properties), obj.evidence_ids)
    props['definition'] = KnownValue('KNOWN', canonical, obj.evidence_ids)
    if statistics is not None:
        statistics['raw_sha_match' if exact else 'content_sha_match'] = 1
    return replace(obj, properties=props, projection=projection,
                   coverage=replace(obj.coverage, ddl='COMPLETE')), ()


def project_target_object(obj, *, source=None, statistics=None):
    """Hedef paket aynıysa kaynak çözümlemesini kullanır, farklıysa parser çağırır."""
    if obj.raw_ddl is None: return obj,()
    reused = _matching_package(obj, source, statistics)
    if reused is not None:
        return reused
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
