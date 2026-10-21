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

INVENTORY_VERSION='source-header-inventory/1.4'


def inspect_artifact(artifact, profile, result):
    record = {'path':artifact.path, 'kind':artifact.kind, 'owner':artifact.source_schema,
              'sha256':artifact.sha256, 'headers':[], 'errors':[], 'tainted_types':[],
              'context_tainted_types':[], 'create_count':0,'package_unit_closed':None,
              'comment_headers':[], 'comment_inventory_closed':False,
              'identity_neutral_context_types':[]}
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
    record['comment_headers'],record['comment_inventory_closed']=_comment_headers(
        tokens,text,artifact.source_schema,require_full=artifact.kind=='COMMENT')
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
        if artifact.kind=='COMMENT' and record['comment_inventory_closed']:
            record['tainted_types']=[kind for kind in record['tainted_types'] if kind!='COMMENT']
        if _neutral_insert_suffix(artifact,result,record):
            record['tainted_types']=[]
    if ('PARSER_SYNTAX_ERROR' in result.diagnostics and any(t.upper=='INSERT' for t in tokens)
            and len(record['headers'])==1 and record['headers'][0]['kind']=='FUNCTION'
            and not _neutral_insert_suffix(artifact,result,record)):
        record['tainted_types']=sorted(set((*record['tainted_types'],'FUNCTION')))
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
            if token.upper=='COMMENT' and not record['comment_inventory_closed']:contexts.add('COMMENT')
            if token.upper in {'GRANT','REVOKE'}:contexts.add('GRANT')
            if token.upper in {'ALTER','DROP','TRUNCATE'}:
                kind=tokens[i+1].upper if i+1<len(tokens) else ''
                affected={'TABLE':{'TABLE','INDEX','TRIGGER','COMMENT','GRANT'},'INDEX':{'INDEX'},'TRIGGER':{'TRIGGER'},
                    'VIEW':{'VIEW'},'PACKAGE':{'PACKAGE_SPEC','PACKAGE_BODY'},
                    'TYPE':{'TYPE_SPEC','TYPE_BODY'},'PROCEDURE':{'PROCEDURE'},'FUNCTION':{'FUNCTION'},
                    'SEQUENCE':{'SEQUENCE'},'SYNONYM':{'SYNONYM'}}.get(kind,set(profile.object_types))
                contexts.update(affected)
        record['context_tainted_types']=sorted(contexts)
        if contexts=={'TRIGGER'} and _only_trigger_state_suffix(tokens,text,record):
            record['identity_neutral_context_types']=['TRIGGER']
    return record


def _comment_headers(tokens,text,default_schema,*,require_full=False):
    """Closed literal COMMENT statements, with their original byte spans."""
    from .statements import qualified_parts,literal_value
    headers=[];covered=set()
    try:
        for index,token in enumerate(tokens):
            if token.upper!='COMMENT':continue
            end=next(i for i in range(index+1,len(tokens)) if tokens[i].text==';')
            statement=tokens[index:end]
            words=[item.upper for item in statement]
            if words[:3] in (['COMMENT','ON','TABLE'],['COMMENT','ON','COLUMN']):
                first=3
            elif words[:4]==['COMMENT','ON','MATERIALIZED','VIEW']:
                first=4
            else:return headers,False
            boundary=words.index('IS',first)
            if len(statement)!=boundary+2:return headers,False
            literal_value(statement[-1].text)
            parts=qualified_parts(statement[first:boundary])
            column=None
            if words[2]=='COLUMN':
                if len(parts)==2:owner,target,column=default_schema,*parts
                elif len(parts)==3:owner,target,column=parts
                else:return headers,False
            elif len(parts)==1:owner,target=default_schema,parts[0]
            elif len(parts)==2:owner,target=parts
            else:return headers,False
            if owner!=Identifier.parse(default_schema).effective_name:return headers,False
            name='S_'+digest(['COMMENT',owner,target,column,None,None])
            headers.append({'owner':owner,'target':target,'column':column,'name':name,
                'start_byte':len(text[:token.start].encode()),'end_byte':len(text[:tokens[end].end].encode())})
            covered.update(range(index,end+1))
        if require_full:
            # COMMENT artifacts are executable scripts. A literal header does
            # not close an unrelated anonymous block or command in that file.
            for index,token in enumerate(tokens):
                if index in covered:continue
                if token.text!='/':return headers,False
                line_start=text.rfind('\n',0,token.start)+1
                line_end=text.find('\n',token.end)
                if line_end<0:line_end=len(text)
                if text[line_start:token.start].strip() or text[token.end:line_end].strip():
                    return headers,False
        return headers,True
    except (ValueError,StopIteration,IndexError):
        return headers,False


def _neutral_insert_suffix(artifact,result,record):
    """A grammar-closed data INSERT cannot define another schema object."""
    if len(artifact.raw)>64*1024 or len(record['headers'])!=1 or record['headers'][0]['kind']!='FUNCTION':
        return False
    start=record['headers'][0]['start_byte']
    source=artifact.raw[start:].decode('utf-8').strip()
    if source.endswith('/'):source=source[:-1].rstrip()
    from antlr4 import CommonTokenStream,InputStream,Token
    from .._vendor.analyzer_core.oracle.ddl_tokens import _Errors
    from .._vendor.analyzer_core.oracle.generated.PlSqlLexer import PlSqlLexer
    from .._vendor.analyzer_core.oracle.generated.PlSqlParser import PlSqlParser
    lexer=PlSqlLexer(InputStream(source));errors=_Errors()
    lexer.removeErrorListeners();lexer.addErrorListener(errors)
    stream=CommonTokenStream(lexer);parser=PlSqlParser(stream)
    parser.removeErrorListeners();parser.addErrorListener(errors)
    parser.create_function_body()
    if errors.count:return False
    if stream.LA(1)==PlSqlParser.SEMICOLON:stream.consume()
    if stream.LT(1).text.upper()!='INSERT':return False
    parser.insert_statement()
    if stream.LA(1)==PlSqlParser.SEMICOLON:stream.consume()
    return errors.count==0 and stream.LA(1)==Token.EOF


def _only_trigger_state_suffix(tokens,text,record):
    from .statements import qualified_parts
    alters=[i for i,t in enumerate(tokens) if t.upper=='ALTER']
    if len(alters)!=1 or len(record['headers'])!=1 or record['headers'][0]['kind']!='TRIGGER':return False
    i=alters[0]
    if i==0 or tokens[i-1].text!='/':return False
    suffix=tokens[i:]
    if len(suffix) not in {5,7} or [t.upper for t in suffix[:2]]!=['ALTER','TRIGGER']:
        return False
    if suffix[-1].text!=';' or suffix[-2].upper not in {'ENABLE','DISABLE'}:return False
    try:
        parts=qualified_parts(suffix[2:-2]);header=record['headers'][0]
        return parts in {(header['name'],),(header['owner'],header['name'])}
    except ValueError:return False


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
    complete = set(profile.object_types)-{'GRANT'}
    contexts=set(complete)
    if errors:
        complete.clear()
        contexts.clear()
    for record in records:
        complete.difference_update((*record['tainted_types'],
            *(set(record['context_tainted_types'])-set(record['identity_neutral_context_types']))))
        contexts.difference_update((*record['tainted_types'],*record['context_tainted_types']))
        if not record['comment_inventory_closed']:
            complete.discard('COMMENT');contexts.discard('COMMENT')
    if not _verified_comments(records,snapshot):
        complete.discard('COMMENT');contexts.discard('COMMENT')
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
        'Sabit kaynak dosyalarının lexer, CREATE başlık ve COMMENT kimlik envanteri; DDL semantiğini doğrulamaz.')
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
    allowed = set(profile['object_types'])-{'GRANT'}
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
                or not isinstance(record['comment_headers'],list)
                or not isinstance(record['comment_inventory_closed'],bool)
                or not isinstance(record['identity_neutral_context_types'],list)
                or not set(record['identity_neutral_context_types']).issubset({'TRIGGER'} & set(record['context_tainted_types']))
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
        derived.difference_update((*record['tainted_types'],
            *(set(record['context_tainted_types'])-set(record['identity_neutral_context_types']))))
        context_derived.difference_update((*record['tainted_types'],*record['context_tainted_types']))
        if not record['comment_inventory_closed']:
            derived.discard('COMMENT');context_derived.discard('COMMENT')
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
    if not _verified_comments(records,snapshot):
        derived.discard('COMMENT');context_derived.discard('COMMENT')
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


def _verified_comments(records,snapshot):
    """Every lexed comment identity must have an attributed canonical object."""
    return _comment_identity_names(records,snapshot,require_parent=True) is not None


def verified_comment_identity_names(snapshot):
    """Closed COMMENT target names even when an unrelated parent is ambiguous.

    A target comment can only be absent when its (owner, synthetic name) is
    absent from this set. A declared name with an unresolved parent remains
    unknown; this API never claims that particular parent identity is absent.
    """
    if not verified_inventory_types(snapshot):return None
    try:
        proof=thaw(snapshot.capabilities['source_inventory_proof'].value)
        records=proof['artifacts']
        if any(not r['comment_inventory_closed'] or 'COMMENT' in
               (*r['tainted_types'],*r['context_tainted_types']) or r['errors'] for r in records):return None
        return _comment_identity_names(records,snapshot,require_parent=False)
    except (ValueError,TypeError,KeyError,AttributeError,IndexError):
        return None


def _comment_identity_names(records,snapshot,*,require_parent):
    registry={ev.id:ev for ev in snapshot.evidence}
    objects={}
    for obj in snapshot.objects:
        if obj.identity.object_type=='COMMENT':
            objects.setdefault((obj.identity.owner.effective_name,obj.identity.name.effective_name),[]).append(obj)
    parents={}
    for obj in snapshot.objects:
        if obj.identity.object_type in {'TABLE','VIEW','MATERIALIZED_VIEW'}:
            parents.setdefault((obj.identity.owner.effective_name,obj.identity.name.effective_name),[]).append(obj)
    seen=set();names=set()
    for record in records:
        for header in record['comment_headers']:
            key=(header['owner'],header['name'])
            if header['owner'] not in snapshot.schemas:continue
            names.add(key)
            if header['name']!='S_'+digest(['COMMENT',header['owner'],header['target'],header['column'],None,None]):return None
            candidates=parents.get((header['owner'],header['target']),())
            matches=[]
            for obj in objects.get(key,()):
                if obj.coverage.inventory!='COMPLETE':continue
                if require_parent and (len(candidates)!=1 or obj.identity.parent_key!=candidates[0].object_key):continue
                if any((value:=obj.properties.get(field)) is None or value.state!='KNOWN' or value.value!=header[field]
                       for field in ('owner','target','column')):continue
                if any(ev_id in registry and registry[ev_id].kind=='SOURCE_SPAN'
                    and registry[ev_id].side=='SOURCE' and registry[ev_id].path==record['path']
                    and registry[ev_id].sha256==record['sha256']
                    and registry[ev_id].start_byte==header['start_byte']
                    and registry[ev_id].end_byte in {header['end_byte'],header['end_byte']-1}
                    for ev_id in obj.evidence_ids):matches.append(obj)
            if not matches:return None
            seen.update(obj.object_key for obj in matches)
    return frozenset(names) if seen=={obj.object_key for group in objects.values() for obj in group} else None


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
