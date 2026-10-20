"""Object-specific decisions. Only verified source statements become intents."""
import re

from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens, identifier, enclosed
from ..model.plan import DependencyReference
from .builder import operation
from .table_ddl import qualified, source_projection


def value(obj,key):
    item = obj.properties.get(key)
    return item.value if item and item.state=='KNOWN' else None


def replace_header(raw):
    # Only the CREATE header changes; body literals and comments stay byte exact.
    text = raw.decode('utf-8')
    tokens = code_tokens(text)
    if not tokens or tokens[0].upper!='CREATE':
        raise ValueError('CREATE_HEADER_UNVERIFIED')
    if tokens[1].upper!='OR':
        text = text[:tokens[0].end]+' OR REPLACE'+text[tokens[0].end:]
    return text.encode('utf-8')


def _index(context,obj,changes):
    projection = source_projection(obj)
    props = projection.properties if projection else {}
    if props.get('availability','VALID')!='VALID':
        return operation(context,obj,changes,'REVIEW','REVIEW_REQUIRED','INDEX_AVAILABILITY_REQUIRES_REVIEW',
                         'Kaynak index UNUSABLE durumundadır; sessizce kullanılabilir index oluşturulmaz.')
    text = obj.raw_ddl.decode() if obj.raw_ddl else ''
    tokens = code_tokens(text) or ()
    words = [t.upper for t in tokens]
    unsupported = any(word in words for word in ('BITMAP','INDEXTYPE','PARTITION','SUBPARTITION'))
    try:
        at = words.index('ON')+1
        opening = next(i for i in range(at,len(tokens)) if tokens[i].text=='(')
        from ..parsing.statements import qualified_parts
        names = qualified_parts(tokens[at:opening])
        owner,name = (obj.identity.owner.effective_name,names[0]) if len(names)==1 else names
        group=enclosed(tokens,opening)
        if group is None: raise ValueError('INDEX_KEYS_UNVERIFIED')
        table = context.lookup(owner,'TABLE',name)
        if table is None: table=context.lookup(owner,'TABLE',name,desired=False)
        if table is None:
            return operation(context,obj,changes,'REVIEW','BLOCKED','INDEX_PARENT_MISSING',
                             f'İndeksin bağlı olduğu {owner}.{name} [TABLE] kaynak ve hedef envanterinde bulunamadı.')
        from .index_rules import index_key_columns
        columns,expression,index_evidence=index_key_columns(context,table,group[0])
        unique = 'UNIQUE' in words[:at]
        if context.new_table(owner,name) and unique and not expression:
            table_projection = source_projection(table)
            for constraint_name,definition in (table_projection.properties.get('constraints',{}) if table_projection else {}).items():
                from .._vendor.analyzer_core.oracle.table import constraint_properties
                details = constraint_properties(definition)
                named_columns=[identifier(t)[0] for t in code_tokens(details['columns'] or '') if t.text!=',']
                from .backing_index import explicit_association
                implicit_name=(obj.identity.name.effective_name==constraint_name or
                               obj.identity.name.effective_name.startswith('SYS_C') and constraint_name.startswith('@anonymous-'))
                if (implicit_name and columns==tuple(named_columns) and details['kind'] in {'PRIMARY KEY','UNIQUE'}
                        and details.get('enabled')!='DISABLE' and not explicit_association(definition)):
                    return operation(context,obj,changes,'PRESERVE','INFORMATIONAL','BACKING_INDEX_CREATED_BY_CONSTRAINT',
                                     'Yeni tablonun PK/UK constraint backing index tanımı ikinci kez oluşturulmaz.')
        if unsupported: raise ValueError('INDEX_FEATURE_UNSUPPORTED')
        if unique and not context.new_table(owner,name) and not expression:
            from .backing_index import existing_backing_index
            proof=existing_backing_index(context,obj,table,tuple(columns))
            if proof:
                return operation(context,obj,changes,'PRESERVE','INFORMATIONAL','EXISTING_BACKING_INDEX_PRESERVED',
                                 'Eşdeğer PK/UK indeksi hedefte mevcut.',extra_evidence_ids=proof)
        if obj.identity.name.effective_name.startswith(('SYS_','ISEQ$$_','BIN$')):
            return operation(context,obj,changes,'REVIEW','BLOCKED','RESERVED_INTERNAL_OBJECT',
                             'Oracle iç indeksinin PK/UK ilişkisi doğrulanamadı.')
        decision = 'REVIEW_REQUIRED' if unique and not context.new_table(owner,name) else 'READY'
        return operation(context,obj,changes,'CREATE_INDEX',decision,'UNIQUE_INDEX_REQUIRES_DATA_REVIEW' if decision!='READY' else 'CREATE_VERIFIED_INDEX',
                         'Index tanımı ve tablo bağımlılığı korunur; mevcut veride unique doğrulaması ayrıca gerekir.' if unique else 'Doğrulanan tablo üzerinde normal index oluşturulacak.',
                         statement=obj.raw_ddl,phase=35,references=(DependencyReference(owner,'TABLE',name,'INDEX_TABLE',tuple(columns)),),extra_evidence_ids=index_evidence)
    except (ValueError,KeyError,TypeError,StopIteration) as error:
        if str(error).startswith('INDEX_EXPRESSION_'):
            return operation(context,obj,changes,'REVIEW','REVIEW_REQUIRED',str(error),
                             'İndeks ifadesinin tip, fonksiyon ve NLS koşulları ayrıca doğrulanmalı.')
        return operation(context,obj,changes,'REVIEW','BLOCKED','INDEX_DEFINITION_UNVERIFIED','Index türü, kolonları veya parent tablo doğrulanamadı.')


def object_change(context,obj,actual,changes):
    kind = obj.identity.object_type
    missing = actual is None
    def decide(decision,code,text,*,statement=None,op_kind='REVIEW',phase=60,refs=(),plsql=False):
        return [operation(context,obj,changes,op_kind,decision,code,text,statement=statement,
                          phase=phase,references=refs,statement_kind='PLSQL' if plsql else 'SQL')]
    if kind=='INDEX':
        return [_index(context,obj,changes)] if missing else decide('REVIEW_REQUIRED','EXISTING_INDEX_CHANGE_REQUIRES_REVIEW','Mevcut index DROP/CREATE ile değiştirilmez.')
    if kind=='SEQUENCE':
        if not missing and all(d.kind=='INFORMATIONAL' for d in changes):
            return decide('INFORMATIONAL','SEQUENCE_COUNTER_PRESERVED','Hedef sequence sayacı korunur.',op_kind='PRESERVE')
        if missing:
            sequence_owner,sequence_name=obj.identity.owner.effective_name,obj.identity.name.effective_name
            existing_consumers=context.existing_sequence_consumers(sequence_owner,sequence_name)
            if existing_consumers:
                return decide('REVIEW_REQUIRED','SEQUENCE_EXISTING_DATA_COLLISION_UNKNOWN','Yeni sequence mevcut tüketicilerde kullanılacak; başlangıcın mevcut verilerle uyumu bilinmiyor.')
            from ..compare.projection_adapter import canonical_fields
            fields = canonical_fields(obj,context.source,context.profile.policy)
            increment = fields.get('/sequence/increment_by')
            if increment and increment.value=='0':
                return decide('BLOCKED','INVALID_SEQUENCE_INCREMENT','Sequence increment sıfır olamaz.')
            return decide('READY','CREATE_MISSING_SEQUENCE','Hedefte bulunmayan sequence kaynak tanımıyla oluşturulacak.',statement=obj.raw_ddl,op_kind='CREATE',phase=10)
        return decide('REVIEW_REQUIRED','SEQUENCE_STATE_PRESERVED','Mevcut sequence ayarları sayaç etkisi incelemesi gerektiriyor; reset üretilmez.')
    if kind in {'COMMENT','GRANT'}:
        parent = context.source_objects.get(obj.identity.parent_key) or context.target_objects.get(obj.identity.parent_key)
        if parent is None:
            return decide('BLOCKED','SIDECAR_PARENT_UNVERIFIED','Comment/grant parent nesnesi doğrulanamadı.')
        refs = (DependencyReference(parent.identity.owner.effective_name,parent.identity.object_type,parent.identity.name.effective_name,'SIDECAR_PARENT'),)
        if kind=='COMMENT':
            target = qualified(parent.identity)
            column = value(obj,'column')
            if column:
                from ..parsing.statements import quote_identifier
                target += '.'+quote_identifier(column)
                refs=(DependencyReference(parent.identity.owner.effective_name,parent.identity.object_type,
                                          parent.identity.name.effective_name,'SIDECAR_PARENT',(column,)),)
            content = value(obj,'text')
            if content is None:
                return decide('REVIEW_REQUIRED','COMMENT_REMOVAL_REQUIRES_REVIEW','Comment silinmesi inceleme gerektiriyor.')
            statement = ('COMMENT ON '+('COLUMN ' if column else 'TABLE ')+target+" IS '"+content.replace("'","''")+"';").encode()
            return decide('READY','SET_VERIFIED_COMMENT','Kaynak yorum içeriği korunarak SQL üretildi.',statement=statement,op_kind='COMMENT',phase=80,refs=refs)
        grantee,privilege = value(obj,'grantee'),value(obj,'privilege')
        known_grantees = context.target.capabilities.get('grantees')
        allowed = (grantee in context.profile.policy.grant_allowlist and known_grantees and known_grantees.state=='KNOWN'
                   and grantee in known_grantees.value and privilege in {'SELECT','INSERT','UPDATE','DELETE','EXECUTE','REFERENCES','READ'}
                   and value(obj,'grantable') is False)
        compatible={'TABLE':{'SELECT','READ','INSERT','UPDATE','DELETE','REFERENCES'},'VIEW':{'SELECT','READ','INSERT','UPDATE','DELETE'},
                    'SEQUENCE':{'SELECT'},'PACKAGE_SPEC':{'EXECUTE'},'PROCEDURE':{'EXECUTE'},'FUNCTION':{'EXECUTE'},'TYPE_SPEC':{'EXECUTE'}}
        allowed=allowed and privilege in compatible.get(parent.identity.object_type,set())
        if value(obj,'column_grant'):
            return decide('BLOCKED','COLUMN_GRANT_UNSUPPORTED','Kolon düzeyinde grant otomatik üretilmez.')
        from ..parsing.statements import quote_identifier
        statement = f'GRANT {privilege} ON {qualified(parent.identity)} TO {quote_identifier(grantee)};'.encode() if allowed else None
        return decide('READY' if allowed else 'REVIEW_REQUIRED','ALLOWLISTED_VERIFIED_GRANT' if allowed else 'GRANT_REQUIRES_REVIEW',
                      'Grant alıcısı, policy ve privilege birlikte doğrulanır.',statement=statement,op_kind='GRANT',phase=90,refs=refs)
    if kind in {'VIEW','PACKAGE_SPEC','PACKAGE_BODY','PROCEDURE','FUNCTION','TYPE_SPEC','TYPE_BODY','TRIGGER'}:
        if any(diff.kind=='UNKNOWN' for diff in changes):
            return decide('BLOCKED','OBJECT_METADATA_INCOMPLETE','Kaynak veya hedef birimin gerekli tanım/edition metadata kanıtı eksik.')
        if any(diff.property_path=='/editionable' for diff in changes):
            return decide('BLOCKED','EDITIONABILITY_CHANGE_UNSUPPORTED','Mevcut nesnenin editionable özelliği CREATE OR REPLACE ile değiştirilemez.')
        words=[t.upper for t in code_tokens(obj.raw_ddl.decode()) or ()]
        declared=obj.properties.get('dependencies')
        tokens=code_tokens(obj.raw_ddl.decode()) or ()
        declared_complete=bool(declared and declared.state=='KNOWN')
        from ..parsing.dependencies import has_dynamic_sql
        if has_dynamic_sql(obj):
            return decide('REVIEW_REQUIRED','DYNAMIC_SQL_DEPENDENCY_REQUIRES_REVIEW',
                          'Dinamik SQL içindeki nesne ve çalışma zamanı etkileri ayrıca incelenmeli.')
        if kind=='TYPE_BODY' and not declared_complete:
            return decide('REVIEW_REQUIRED','TYPE_BODY_DEPENDENCY_INVENTORY_REQUIRED','Type body parametre ve çağrı bağımlılık envanteri doğrulanmalı.')
        # Qualified declarations, %TYPE/%ROWTYPE and code references not covered
        # by a complete exporter inventory remain a review requirement. The
        # CREATE owner.name itself is the first dot and is not a dependency.
        qualified_uses=sum(token.text=='.' for token in tokens)
        own_qualified=any(tokens[i].text=='.' and i>0 and i+1<len(tokens)
                          and tokens[i-1].text.strip('"').upper()==obj.identity.owner.effective_name.upper()
                          and tokens[i+1].text.strip('"').upper()==obj.identity.name.effective_name.upper()
                          for i in range(min(len(tokens),12)))
        if kind in {'PROCEDURE','FUNCTION','PACKAGE_SPEC','PACKAGE_BODY'} and not declared_complete and qualified_uses>int(own_qualified):
            return decide('REVIEW_REQUIRED','QUALIFIED_REFERENCE_INVENTORY_REQUIRED','Qualified çağrı, type veya değişken referansının tam bağımlılık envanteri doğrulanmalı.')
        if kind in {'PACKAGE_SPEC','PACKAGE_BODY','PROCEDURE','FUNCTION'} and (any(word in words for word in ('SELECT','INSERT','UPDATE','DELETE','MERGE','EXECUTE'))
                             and not (declared and declared.state=='KNOWN')):
            return decide('REVIEW_REQUIRED','ROUTINE_DEPENDENCY_INVENTORY_REQUIRED','SQL veya dynamic SQL içeren birimin bağımlılık envanteri doğrulanmalı.')
        if kind.startswith('TYPE') and not missing:
            return decide('BLOCKED','EXISTING_TYPE_EVOLUTION_UNSUPPORTED','Mevcut type evrimi otomatik üretilmez.')
        if not missing and kind=='PACKAGE_SPEC':
            return decide('REVIEW_REQUIRED','PUBLIC_PACKAGE_CONTRACT_REQUIRES_REVIEW','Package spec değişimi çağıranların sözleşme incelemesini gerektiriyor.')
        if kind=='TRIGGER':
            if not missing:
                return decide('REVIEW_REQUIRED','TRIGGER_RUNTIME_EFFECT_REQUIRES_REVIEW','Mevcut trigger değişimi veri etkisi incelemesi gerektiriyor.')
            from ..parsing.statements import qualified_parts
            try:
                at=words.index('ON')+1;finish=at+3 if at+1<len(tokens) and tokens[at+1].text=='.' else at+1
                names=qualified_parts(tokens[at:finish]);owner,name=(obj.identity.owner.effective_name,names[0]) if len(names)==1 else names
                if not context.new_table(owner,name) or 'COMPOUND' in words or 'SCHEMA' in words or 'DATABASE' in words:
                    raise ValueError('TRIGGER_EMPTY_TABLE_NOT_PROVEN')
                projection=source_projection(obj);state=projection.properties.get('enabled_state') if projection else None
                if state not in {None,'ENABLE','DISABLE','ENABLED','DISABLED'}: raise ValueError('TRIGGER_STATE_UNKNOWN')
                statement=replace_header(obj.raw_ddl)
                source_body=next(i for i,t in enumerate(tokens) if t.upper in {'DECLARE','BEGIN','CALL'})
                from .trigger_rules import sequence_only_insert
                table=context.lookup(owner,'TABLE',name)
                verified_assignment=bool(table and sequence_only_insert(context,obj,table,tokens,source_body))
                if not declared_complete and not verified_assignment and any(t.upper not in {'BEGIN','END','NULL',';'} for t in tokens[source_body:]):
                    raise ValueError('TRIGGER_CODE_DEPENDENCY_INVENTORY_REQUIRED')
                if not declared_complete and not verified_assignment and any(t.upper in {'DECLARE','SELECT','INSERT','UPDATE','DELETE','MERGE','EXECUTE','CALL'} for t in tokens[source_body:]):
                    raise ValueError('TRIGGER_CODE_DEPENDENCY_UNVERIFIED')
                if state in {'DISABLE','DISABLED'}:
                    text=statement.decode();updated=code_tokens(text);body=next(token for token in updated if token.upper in {'DECLARE','BEGIN','CALL'})
                    # An explicitly present header state must be handled rather
                    # than duplicated. New unmodelled forms stay blocked.
                    header=text[:body.start]
                    if any(token.upper in {'ENABLE','DISABLE'} for token in code_tokens(header)):
                        raise ValueError('TRIGGER_HEADER_STATE_REQUIRES_REVIEW')
                    statement=(text[:body.start]+'DISABLE '+text[body.start:]).encode()
                return decide('READY','CREATE_TRIGGER_ON_NEW_EMPTY_TABLE','Yeni boş tablonun trigger tanımı ve enabled durumu korunur.',
                              statement=statement,op_kind='CREATE',phase=70,
                              refs=(DependencyReference(owner,'TABLE',name,'TRIGGER_TABLE'),),plsql=True)
            except (ValueError,StopIteration,TypeError):
                return decide('REVIEW_REQUIRED','TRIGGER_RUNTIME_EFFECT_REQUIRES_REVIEW','Trigger parent, enabled durumu veya veri etkisi inceleme gerektiriyor.')
        refs = []
        if kind in {'PROCEDURE','FUNCTION'}:
            projection=source_projection(obj)
            if projection is None or '_generator_routine_analysis' not in projection.properties:
                from ..parsing.adapter import parse_ddl
                from dataclasses import replace
                parsed=parse_ddl(obj.raw_ddl,obj.identity)
                candidate=next((item for item in parsed.objects if item.identity.key==obj.object_key and item.parse_ok and not item.diagnostics),None)
                if candidate is None:
                    return decide('BLOCKED','ROUTINE_DEPENDENCY_ANALYSIS_UNAVAILABLE','Routine parametre ve çağrı analizi doğrulanamadı.')
                analyzed=replace(obj,projection=candidate.projection)
            else: analyzed=obj
            from ..parsing.dependencies import references
            refs.extend(references(analyzed))
        if kind.endswith('_BODY'):
            refs.append(DependencyReference(obj.identity.owner.effective_name,kind.replace('_BODY','_SPEC'),obj.identity.name.effective_name,'SPEC'))
        # FORCE is an installation behavior, never a substitute for dependencies.
        statement = replace_header(obj.raw_ddl)
        if kind=='VIEW':
            statement = re.sub(rb'(?i)^(\s*CREATE\s+OR\s+REPLACE\s+(?:(?:NON)?EDITIONABLE\s+)?)FORCE\s+',rb'\1',statement,count=1)
        return decide('READY','CREATE_VERIFIED_OBJECT' if missing else 'REPLACE_VERIFIED_OBJECT',
                      'Doğrulanan kaynak birimi bağımlılık denetiminden sonra üretilecek.',statement=statement,
                      op_kind='CREATE' if missing else 'REPLACE',phase=55 if kind.endswith('_SPEC') else 60,refs=tuple(refs),plsql=kind!='VIEW')
    if kind=='SYNONYM':
        from ..parsing.statements import qualified_parts
        tokens=code_tokens(obj.raw_ddl.decode()) or ();words=[t.upper for t in tokens]
        if 'PUBLIC' in words or any(t.text=='@' for t in tokens):
            return decide('BLOCKED','PUBLIC_SYNONYM_OR_DATABASE_LINK_UNSUPPORTED','Public synonym veya DB link otomatik üretilemez.')
        try:
            at=words.index('FOR')+1
            names=qualified_parts(tuple(t for t in tokens[at:] if t.text!=';'))
            owner,name=(obj.identity.owner.effective_name,names[0]) if len(names)==1 else names
            return decide('READY','CREATE_VERIFIED_PRIVATE_SYNONYM','Private synonym hedefi bağımlılık grafında doğrulanır.',
                          statement=replace_header(obj.raw_ddl),op_kind='CREATE' if missing else 'REPLACE',phase=75,
                          refs=(DependencyReference(owner,'SYNONYM_OBJECT',name,'SYNONYM_TARGET'),))
        except (ValueError,TypeError):
            return decide('BLOCKED','SYNONYM_TARGET_UNVERIFIED','Synonym hedef kimliği çözümlenemedi.')
    return decide('BLOCKED','OBJECT_FEATURE_UNSUPPORTED','Bu nesne özelliği güvenli otomatik üretim kapsamında değil.')
