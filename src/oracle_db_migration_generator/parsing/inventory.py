"""Evidence-bound CREATE identity coverage, independent of semantic parsing."""
import hashlib
import re
from collections import Counter
from dataclasses import replace

from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens
from .._vendor.analyzer_core.oracle.scanner import scan
from ..model.evidence import Evidence
from ..model.identity import Identifier, ObjectIdentity
from ..model.serialization import digest, thaw
from ..model.snapshot import KnownValue
from .canonicalize import canonical_sql

INVENTORY_VERSION='source-header-inventory/1.2'


def inspect_artifact(artifact, profile, result):
    record = {'path':artifact.path, 'kind':artifact.kind, 'owner':artifact.source_schema,
              'sha256':artifact.sha256, 'headers':[], 'errors':[], 'tainted_types':[],
              'context_tainted_types':[], 'create_count':0,'package_unit_closed':None}
    if hashlib.sha256(artifact.raw).hexdigest()!=artifact.sha256:
        record['errors'].append('INVENTORY_BLOB_HASH_MISMATCH')
        return record
    try:
        text = artifact.raw.decode('utf-8')
    except UnicodeError:
        record['errors'].append('ENCODING_UNRESOLVED')
        return record
    tokens = code_tokens(text)
    scanner_input=text
    if tokens is not None:
        replacements=[]
        for i,token in enumerate(tokens[:-3]):
            if [item.upper for item in tokens[i:i+4]]==['CREATE','GLOBAL','TEMPORARY','TABLE']:
                replacements.extend((item.start,item.end) for item in tokens[i+1:i+3])
        for start,end in reversed(replacements):
            scanner_input=scanner_input[:start]+' '*(end-start)+scanner_input[end:]
    scanned = scan(scanner_input.encode('utf-8'), default_schema=artifact.source_schema)
    if tokens is None or any(code!='UNRESOLVED_PREFIX_OR_ARTIFACT' for code in scanned.diagnostics):
        record['errors'].append('INVENTORY_LEXER_UNVERIFIED')
        return record
    creates = {token.start for token in tokens if token.upper=='CREATE'}
    record['create_count']=len(creates)
    occurrences = [item for item in scanned.occurrences if item.start_char in creates]
    if creates!={item.start_char for item in occurrences}:
        record['errors'].append('INVENTORY_CREATE_HEADER_UNRESOLVED')
        return record
    if occurrences and tokens and tokens[0].start!=occurrences[0].start_char:
        record['errors'].append('INVENTORY_PREFIX_UNRESOLVED')
    if not occurrences and not result.sidecars and artifact.kind not in {'COMMENT','GRANT'}:
        record['errors'].append('INVENTORY_SCRIPT_UNRESOLVED')
    owner = Identifier.parse(artifact.source_schema)
    for index, item in enumerate(occurrences):
        schema = Identifier(item.raw_schema if item.schema_quoted else item.raw_schema.upper(),
                            item.raw_schema, item.schema_quoted)
        name = Identifier(item.raw_name if item.name_quoted else item.raw_name.upper(), item.raw_name, item.name_quoted)
        kind = 'TYPE_SPEC' if item.object_type=='TYPE' else item.object_type
        if schema!=owner or kind not in profile.object_types:
            record['errors'].append('INVENTORY_HEADER_OUTSIDE_PROFILE')
            continue
        identity = ObjectIdentity(profile.id, schema, kind, name)
        end = occurrences[index+1].start_byte if index+1<len(occurrences) else len(artifact.raw)
        end_char = occurrences[index+1].start_char if index+1<len(occurrences) else len(text)
        record['headers'].append({'object_key':identity.key, 'owner':schema.effective_name,
            'kind':kind, 'name':name.effective_name, 'quoted':name.quoted,
            'start_byte':item.start_byte, 'end_byte':end,
            'start_line':item.start_line, 'end_line':text.count('\n',0,end_char)+1})
    if 'UNSUPPORTED_STATEMENT' in result.diagnostics:
        record['tainted_types'] = sorted({item['kind'] for item in record['headers']} or
                                        ({artifact.kind} if artifact.kind in {'COMMENT','GRANT'} else set(profile.object_types)))
    if result.coverage!='COMPLETE':
        contexts=set()
        package_headers=[header for header in record['headers'] if header['kind'] in {'PACKAGE_SPEC','PACKAGE_BODY'}]
        closed_package=bool(len(record['headers'])==1 and package_headers and
                            _closed_package_unit(tokens,package_headers[0]['name'],text))
        if package_headers:record['package_unit_closed']=closed_package
        if package_headers and not closed_package:
            contexts.update(profile.object_types)
        for i,token in enumerate(tokens):
            line_start=text.rfind('\n',0,token.start)+1
            first_on_line=i==0 or tokens[i-1].end<=line_start
            command_position=first_on_line or i>0 and tokens[i-1].text in {';','/'}
            following=tokens[i+1].upper if i+1<len(tokens) else ''
            if command_position and token.text=='@':
                contexts.update(profile.object_types)
            if command_position and not closed_package and (
                    token.upper in {'EXEC','CALL'} or
                    token.upper=='EXECUTE' and following!='IMMEDIATE' or
                    token.upper=='CONNECT' and following!='BY' or
                    token.upper=='START' and following not in {'WITH','(',':='} or
                    token.upper=='HOST' and following not in {'(',':='}):
                contexts.update(profile.object_types)
            if token.upper in {'RENAME','FLASHBACK','PURGE','AUDIT','NOAUDIT','ASSOCIATE','DISASSOCIATE'}:
                contexts.update(profile.object_types)
            if token.upper=='COMMENT':contexts.add('COMMENT')
            if token.upper in {'GRANT','REVOKE'}:contexts.add('GRANT')
            if token.upper in {'ALTER','DROP','TRUNCATE'}:
                kind=tokens[i+1].upper if i+1<len(tokens) else ''
                affected={'TABLE':{'TABLE','INDEX','TRIGGER','COMMENT','GRANT'},'INDEX':{'INDEX'},'TRIGGER':{'TRIGGER'},
                    'VIEW':{'VIEW'},'PACKAGE':{'PACKAGE_SPEC','PACKAGE_BODY'},
                    'TYPE':{'TYPE_SPEC','TYPE_BODY'},'PROCEDURE':{'PROCEDURE'},'FUNCTION':{'FUNCTION'},
                    'SEQUENCE':{'SEQUENCE'},'SYNONYM':{'SYNONYM'}}.get(kind,set(profile.object_types))
                contexts.update(affected)
        record['context_tainted_types']=sorted(contexts)
    return record


def _closed_package_unit(tokens,name,text):
    for i,token in enumerate(tokens[:-1]):
        if token.text!='/':continue
        line_start=text.rfind('\n',0,token.start)+1
        line_end=text.find('\n',token.end)
        if line_end<0:line_end=len(text)
        if (i==0 or tokens[i-1].end<=line_start) and tokens[i+1].start>=line_end:
            return False
    tail=tokens[:-1] if tokens and tokens[-1].text=='/' else tokens
    if len(tail)<2 or tail[-1].text!=';':return False
    if tail[-2].upper=='END':return True
    if len(tail)<3 or tail[-3].upper!='END':return False
    try:
        return Identifier.parse(tail[-2].text).effective_name==name
    except ValueError:
        return False


def fallback_objects(artifact, profile, result, record, parsed_class):
    if result.objects or not {'PARSER_TIMEOUT','PARSER_WORKER_TERMINATED'} & set(result.diagnostics) or record['errors']:
        return result
    objects = []
    for header in record['headers']:
        owner = Identifier(header['owner'], header['owner'], True)
        name = Identifier(header['name'], header['name'], header['quoted'])
        identity = ObjectIdentity(profile.id, owner, header['kind'], name)
        start, end = header['start_byte'], header['end_byte']
        objects.append(parsed_class(identity, None, artifact.raw[start:end], start, end,
            header['start_line'], header['end_line'], False, tuple(sorted(set((*result.diagnostics,'HEADER_IDENTITY_ONLY'))))))
    return replace(result, objects=tuple(objects))


def attach_inventory_proof(snapshot, inputs, profile, records):
    keys = [header['object_key'] for record in records for header in record['headers']]
    duplicate_keys={key for key,count in Counter(keys).items() if count>1}
    blobs={artifact.path:artifact.raw for artifact in inputs.artifacts}
    objects={obj.object_key:obj for obj in snapshot.objects}
    registry={ev.id:ev for ev in snapshot.evidence}
    for record in records:
        for header in record['headers']:
            if header['object_key'] in duplicate_keys:
                obj=objects.get(header['object_key'])
                spans=[registry[key] for key in obj.evidence_ids if key in registry
                       and registry[key].kind=='SOURCE_SPAN' and registry[key].path==record['path']
                       and registry[key].sha256==record['sha256']
                       and registry[key].start_byte==header['start_byte']
                       and registry[key].end_byte is not None and registry[key].end_byte<=header['end_byte']] if obj else []
                if len(spans)==1:
                    header['definition_evidence_id']=spans[0].id
                    header['definition_end_byte']=spans[0].end_byte
                raw=blobs[record['path']][header['start_byte']:header.get('definition_end_byte',header['end_byte'])]
                header['definition_fingerprint']=hashlib.sha256(canonical_sql(raw.decode('utf-8')).encode()).hexdigest()
    errors = any(record['errors'] for record in records) or not _equivalent_duplicates(records,snapshot)
    complete = set(profile.object_types)-{'COMMENT','GRANT'}
    contexts=set(complete)
    if errors:
        complete.clear()
        contexts.clear()
    for record in records:
        complete.difference_update((*record['tainted_types'],*record['context_tainted_types']))
        contexts.difference_update((*record['tainted_types'],*record['context_tainted_types']))
    if 'SOURCE_SIDECAR_UNRESOLVED' in snapshot.completeness.diagnostics:
        contexts.clear()
    proof = {'version':INVENTORY_VERSION, 'source_commit':snapshot.source_commit,
        'source_input_digest':inputs.input_digest, 'source_profile_sha256':digest(profile),
        'profile':thaw(profile),
        'files':[[item.path,item.kind,item.sha256] for item in inputs.artifacts],
        'schemas':list(snapshot.schemas), 'complete_types':sorted(complete),
        'context_complete_types':sorted(contexts),
        'parser_diagnostics':list(snapshot.completeness.diagnostics), 'artifacts':records}
    proof_hash = digest(proof)
    evidence = Evidence('ev-'+proof_hash, 'ABSENCE_SCOPE', 'SOURCE', None, proof_hash, None, None, None,
        'Sabit kaynak dosyalarının lexer ve CREATE başlık envanteri; DDL semantiğini doğrulamaz.')
    return replace(snapshot, capabilities={**snapshot.capabilities,
        'source_inventory_proof':KnownValue('KNOWN', proof, (evidence.id,))}, evidence=(*snapshot.evidence,evidence))


def verified_inventory_types(snapshot, *, context=False):
    """Validate once per comparison; malformed or detached proof is conservative."""
    try:
        return _verified_inventory_types(snapshot,context=context)
    except (ValueError,TypeError,KeyError,AttributeError,IndexError):
        return frozenset()


def _verified_inventory_types(snapshot, *, context=False):
    if snapshot.side!='SOURCE':
        return frozenset()
    value = snapshot.capabilities.get('source_inventory_proof')
    if value is None or value.state!='KNOWN' or len(value.evidence_ids)!=1:
        return frozenset()
    proof = thaw(value.value)
    if not isinstance(proof,dict) or proof.get('version')!=INVENTORY_VERSION:
        return frozenset()
    registry = {ev.id:ev for ev in snapshot.evidence}
    proof_hash = digest(proof)
    evidence = registry.get(value.evidence_ids[0])
    if (evidence is None or evidence.id!='ev-'+proof_hash or evidence.sha256!=proof_hash
            or evidence.side!='SOURCE' or evidence.kind!='ABSENCE_SCOPE'
            or proof.get('source_commit')!=snapshot.source_commit
            or not set(snapshot.schemas).issubset(proof.get('schemas',[]))):
        return frozenset()
    for key, field, kind, side in (('source_input_digest','source_input_digest','ABSENCE_SCOPE','SOURCE'),
                                  ('source_profile_sha256','source_profile_sha256','POLICY','POLICY')):
        cap = snapshot.capabilities.get(key)
        if (cap is None or cap.state!='KNOWN' or cap.value!=proof.get(field)
                or not cap.evidence_ids or any(ev_id not in registry for ev_id in cap.evidence_ids)
                or not any(registry[ev_id].kind==kind and registry[ev_id].side==side
                           and registry[ev_id].sha256==cap.value for ev_id in cap.evidence_ids)):
            return frozenset()
    diagnostic_extra = set(snapshot.completeness.diagnostics)-set(proof.get('parser_diagnostics',[]))
    if diagnostic_extra-({'SOURCE_OWNER_SCOPE_UNVERIFIED'} if 'owner_scope_proof' in snapshot.capabilities else set()):
        return frozenset()
    records = proof.get('artifacts')
    if not isinstance(records,list) or not records or any(not isinstance(record,dict) for record in records):
        return frozenset()
    profile, manifest = proof['profile'],proof['files']
    if (not isinstance(profile,dict) or profile.get('id')!=snapshot.profile_id
            or digest(profile)!=proof['source_profile_sha256'] or not isinstance(manifest,list)):
        return frozenset()
    if digest({'commit':proof['source_commit'],'profile':profile,'files':manifest})!=proof['source_input_digest']:
        return frozenset()
    allowed = set(profile['object_types'])-{'COMMENT','GRANT'}
    if not all(isinstance(kind,str) for kind in allowed):
        return frozenset()
    paths = {}
    for row in manifest:
        if (not isinstance(row,list) or len(row)!=3 or not all(isinstance(item,str) for item in row)
                or not row[0] or ':' in row[0] or '\\' in row[0]
                or any(part in {'','.','..'} for part in row[0].split('/'))
                or not re.fullmatch('[a-f0-9]{64}',row[2]) or row[0] in paths):
            return frozenset()
        paths[row[0]] = row
    expected = {path for path,row in paths.items() if row[1] not in {'MANIFEST','DEPENDENCIES'}}
    if len(records)!=len(expected) or {row['path'] for row in records}!=expected:
        return frozenset()
    derived = set(allowed)
    context_derived=set(allowed)
    all_keys = []
    for record in records:
        if ([record['path'],record['kind'],record['sha256']]!=paths[record['path']]
                or not isinstance(record['headers'],list) or not isinstance(record['errors'],list)
                or not isinstance(record['tainted_types'],list)
                or not isinstance(record['context_tainted_types'],list)
                or record['package_unit_closed'] is not None and not isinstance(record['package_unit_closed'],bool)
                or any(not isinstance(code,str) for code in record['errors'])
                or not set((*record['tainted_types'],*record['context_tainted_types'])).issubset(set(profile['object_types']))
                or not isinstance(record['create_count'],int)
                or not record['errors'] and (record['create_count']!=len(record['headers'])
                    or len({h['start_byte'] for h in record['headers']})!=len(record['headers']))):
            return frozenset()
        roots = [root for root in profile['schema_roots'] if record['path'].startswith(root['path']+'/')]
        if len(roots)!=1 or record['owner']!=roots[0]['source_schema']:
            return frozenset()
        if record['errors']:
            derived.clear()
            context_derived.clear()
        derived.difference_update((*record['tainted_types'],*record['context_tainted_types']))
        context_derived.difference_update((*record['tainted_types'],*record['context_tainted_types']))
        for header in record['headers']:
            if (not isinstance(header,dict) or header['kind'] not in profile['object_types']
                    or header['owner']!=Identifier.parse(record['owner']).effective_name
                    or not isinstance(header['quoted'],bool) or not isinstance(header['name'],str)
                    or not isinstance(header['start_byte'],int) or header['start_byte']<0
                    or not isinstance(header['end_byte'],int) or header['end_byte']<=header['start_byte']):
                return frozenset()
            identity = ObjectIdentity(profile['id'],Identifier(header['owner'],header['owner'],True),
                header['kind'],Identifier(header['name'],header['name'],header['quoted']))
            if identity.key!=header['object_key']:
                return frozenset()
            all_keys.append(header['object_key'])
    if not _equivalent_duplicates(records,snapshot):
        derived.clear()
        context_derived.clear()
    if 'SOURCE_SIDECAR_UNRESOLVED' in proof['parser_diagnostics']:
        context_derived.clear()
    if not isinstance(proof['complete_types'],list) or set(proof['complete_types'])!=derived:
        return frozenset()
    if not isinstance(proof['context_complete_types'],list) or set(proof['context_complete_types'])!=context_derived:
        return frozenset()
    headers = {header['object_key']:header for record in records for header in record.get('headers',[])
               if header.get('owner') in snapshot.schemas}
    objects = {obj.object_key:obj for obj in snapshot.objects if obj.identity.object_type not in {'COMMENT','GRANT'}}
    if headers.keys()!=objects.keys():
        return frozenset()
    for record in records:
        for header in record.get('headers',[]):
            obj = objects.get(header['object_key'])
            if obj is not None and (obj.identity.object_type!=header['kind']
                    or obj.identity.owner.effective_name!=header['owner']
                    or obj.identity.name.effective_name!=header['name']):
                return frozenset()
            if obj is not None and not any(ev_id in registry and registry[ev_id].kind=='SOURCE_SPAN'
                    and registry[ev_id].side=='SOURCE' and registry[ev_id].path==record['path']
                    and registry[ev_id].sha256==record['sha256'] for ev_id in obj.evidence_ids):
                return frozenset()
    return frozenset(context_derived if context else derived)


def _equivalent_duplicates(records,snapshot):
    groups={}
    for record in records:
        for header in record['headers']:groups.setdefault(header['object_key'],[]).append((record,header))
    objects={obj.object_key:obj for obj in snapshot.objects}
    registry={ev.id:ev for ev in snapshot.evidence}
    for key,headers in groups.items():
        if len(headers)<2:continue
        obj=objects.get(key)
        definition=obj.properties.get('definition') if obj is not None else None
        if obj is None or obj.coverage.ddl!='COMPLETE' or definition is None or definition.state!='KNOWN':
            return False
        expected=hashlib.sha256(definition.value.encode()).hexdigest()
        for record,header in headers:
            ev=registry.get(header.get('definition_evidence_id'))
            if (header.get('definition_fingerprint')!=expected or ev is None or ev.id not in obj.evidence_ids
                    or ev.kind!='SOURCE_SPAN' or ev.side!='SOURCE' or ev.path!=record['path']
                    or ev.sha256!=record['sha256'] or ev.start_byte!=header['start_byte']
                    or ev.end_byte!=header.get('definition_end_byte')):
                return False
    return True
