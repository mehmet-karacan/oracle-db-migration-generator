from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens
from .._vendor.analyzer_core.oracle.table import constraint_properties
from ..compare.projection_adapter import canonical_fields, table_columns
from ..model.plan import DependencyReference
from ..parsing.statements import qualified_parts, quote_identifier
from .builder import operation
from .policy import unsupported_table_feature
from .table_ddl import column_definition, datatype_sql, qualified, source_projection, table_base
from .backing_index import backing_reference


def _value(fields,key):
    value = fields.get(key)
    return value.value if value is not None and value.state=='KNOWN' else None


def _collation_capability(context):
    capability=context.target.capabilities.get('data_bound_collation_enabled')
    return (capability.value if capability and capability.state=='KNOWN' and isinstance(capability.value,bool) else None,
            capability.evidence_ids if capability else ())


def _definition_error(error):
    code=str(error)
    return code if code in {'TARGET_COLLATION_CAPABILITY_UNKNOWN','TARGET_COLLATION_SYNTAX_UNAVAILABLE',
                            'SOURCE_COLLATION_UNVERIFIED','SOURCE_COLLATION_CONFLICT'} else 'SOURCE_TABLE_DEFINITION_UNVERIFIED'


def column_fields(obj,snapshot,policy):
    result = table_columns(obj,snapshot)
    if result:
        return result
    for path,value in canonical_fields(obj,snapshot,policy).items():
        parts = path.split('/')
        if len(parts)==4 and parts[1]=='columns':
            name = parts[2].replace('~1','/').replace('~0','~')
            result.setdefault(name,{})[parts[3]] = value
    return result


def _safety_proven(actual,name):
    explicit_partition = actual.properties.get('/columns/'+name+'/partition_key') or actual.properties.get(name+'.partition_key')
    explicit_domain = actual.properties.get('/columns/'+name+'/domain_index_dependency') or actual.properties.get(name+'.domain_index_dependency')
    if explicit_partition and explicit_domain:
        return explicit_partition.state==explicit_domain.state=='KNOWN' and explicit_partition.value is False and explicit_domain.value is False
    keys = actual.properties.get('dictionary.partition_keys')
    indexes = actual.properties.get('dictionary.indexes')
    columns = actual.properties.get('dictionary.index_columns')
    if not keys or not indexes or not columns or any(item.state!='KNOWN' for item in (keys,indexes,columns)):
        return False
    if any(row['column_name']==name for row in keys.value):
        return False
    # A domain index can depend on arbitrary expressions; absent complete
    # dependency proof, conservatively hold widening on the entire table.
    return not any('DOMAIN' in str(row.get('index_type','')) for row in indexes.value)


def _fk_reference(definition,owner):
    tokens = code_tokens(definition)
    words = [token.upper for token in tokens]
    at = words.index('REFERENCES')+1
    opening = next(i for i in range(at,len(tokens)) if tokens[i].text=='(')
    names = qualified_parts(tokens[at:opening])
    target_owner,target_name = (owner,names[0]) if len(names)==1 else names
    from .._vendor.analyzer_core.oracle.ddl_tokens import identifier
    end=next(i for i in range(opening+1,len(tokens)) if tokens[i].text==')')
    columns=tuple(identifier(token)[0] for token in tokens[opening+1:end] if token.text!=',')
    return DependencyReference(target_owner,'TABLE',target_name,'FK_PARENT',columns)


def create_table(context,obj,changes):
    columns = column_fields(obj,context.source,context.profile.policy)
    from .partition_rules import range_layout
    try:layout=range_layout(obj,columns)
    except (ValueError,IndexError,TypeError):
        return [operation(context,obj,changes,'REVIEW','BLOCKED','PARTITION_LAYOUT_UNVERIFIED',
                          'Partition key, sınır, tip veya interval ifadesi üretim için doğrulanamadı.')]
    from .lob_rules import verified_basicfile_lobs
    lob_verified=verified_basicfile_lobs(context,obj,columns)
    if unsupported_table_feature(obj,partition_verified=layout is not None,lob_verified=lob_verified):
        return [operation(context,obj,changes,'REVIEW','BLOCKED','BLOCKED_UNSUPPORTED_FEATURE',
                          'Partition, LOB, IOT, external veya cluster özelliği sade tabloya dönüştürülemez.')]
    unknown=[name+' ('+', '.join({'data_type':'kolon tipi','length':'uzunluk','length_semantics':'uzunluk birimi'}[key]
                                for key in ('data_type','length','length_semantics') if fields[key].state=='UNKNOWN')+')'
             for name,fields in sorted(columns.items())
             if any(fields[key].state=='UNKNOWN' for key in ('data_type','length','length_semantics'))]
    if unknown:
        return [operation(context,obj,changes,'REVIEW','BLOCKED','UNKNOWN_SOURCE_SEMANTICS',
                          'Kaynak kolon bilgisi doğrulanamadı: '+', '.join(unknown)+'.')]
    collation_enabled,capability_ids=_collation_capability(context)
    try:
        statement = table_base(obj,columns_fields=columns,collation_enabled=collation_enabled)
        projection = source_projection(obj)
        if any(any(token.upper=='REFERENCES' for token in code_tokens(detail['definition']) or ())
               for detail in projection.properties.get('columns',{}).values()):
            raise ValueError('INLINE_FOREIGN_KEY_REQUIRES_SEPARATE_CONSTRAINT')
    except (ValueError,KeyError,TypeError,StopIteration) as error:
        return [operation(context,obj,changes,'REVIEW','BLOCKED',_definition_error(error),
                          'Kaynak tablo tanımı veya hedefte collation korunumu üretim için doğrulanamadı.',extra_evidence_ids=capability_ids)]
    result = [operation(context,obj,changes,'CREATE','READY','CREATE_VERIFIED_RANGE_TABLE' if layout else 'CREATE_VERIFIED_BASICFILE_LOB_TABLE' if lob_verified else 'CREATE_VERIFIED_HEAP_TABLE',
                        'Hedefte yokluğu doğrulanan tablo, tüm kolon özellikleri korunarak oluşturulacak.',
                        statement=statement,phase=20,feature_scope='TABLE_BASE',extra_evidence_ids=capability_ids)]
    for name,definition in sorted(projection.properties.get('constraints',{}).items()):
        details = constraint_properties(definition)
        refs = (_fk_reference(definition,obj.identity.owner.effective_name),) if details['kind']=='FOREIGN KEY' else ()
        try:
            backing=backing_reference(context,obj,definition)
            if backing is not None: refs=refs+(backing,)
        except (ValueError,KeyError,TypeError):
            result.append(operation(context,obj,changes,'ADD_CONSTRAINT','BLOCKED','BACKING_INDEX_ASSOCIATION_UNVERIFIED',
                                    'PK/UK için adlandırılmış index tanımı, parent/kolon eşleşmesi veya durumu doğrulanamadı.',
                                    tag='constraint:'+name,feature_scope='CONSTRAINT'))
            continue
        result.append(operation(context,obj,changes,'ADD_CONSTRAINT','READY','ADD_CONSTRAINT_TO_NEW_EMPTY_TABLE',
                                'Yeni boş tablonun constraint tanımı bağımlılık sırasıyla eklenecek; kaynakta adsızsa ad üretilmez.',
                                statement=f'ALTER TABLE {qualified(obj.identity)} ADD {definition};'.encode(),
                                phase=50 if details['kind']=='FOREIGN KEY' else 40,tag='constraint:'+name,references=refs,feature_scope='CONSTRAINT'))
    return result


def change_table(context,desired,actual,changes):
    # Existing partition/LOB storage is not rewritten by an independent ADD,
    # DEFAULT or proven widening. Structural storage conversions stay closed.
    complex_layout=False
    for obj in (desired,actual):
        projection=source_projection(obj)
        props=projection.properties.get('table_properties',{}) if projection else {}
        dictionary=obj.properties.get('dictionary.tables')
        complex_layout |= bool(props.get('external') or props.get('cluster') or
                               props.get('organization') and 'INDEX' in props['organization'].upper())
        complex_layout |= bool(dictionary and dictionary.state=='KNOWN' and
                               any(row.get('iot_type') or row.get('cluster_name') for row in dictionary.value))
    if complex_layout:
        return [operation(context,desired,changes,'REVIEW','BLOCKED','BLOCKED_UNSUPPORTED_FEATURE',
                          'Tablonun kapsanamayan fiziksel özellikleri otomatik dönüşümü engelliyor.')]
    desired_columns = column_fields(desired,context.source,context.profile.policy)
    actual_columns = column_fields(actual,context.target,context.profile.policy)
    groups,other = {},[]
    for diff in changes:
        parts = diff.property_path.split('/')
        if len(parts)>=4 and parts[1]=='columns':
            name = parts[2].replace('~1','/').replace('~0','~')
            groups.setdefault(name,[]).append(diff)
        else:
            other.append(diff)
    result = []
    for name,column_changes in sorted(groups.items()):
        after,before = desired_columns.get(name),actual_columns.get(name)
        if after is None:
            result.append(operation(context,actual,column_changes,'PRESERVE','INFORMATIONAL','TARGET_ONLY_COLUMN_PRESERVED',
                                    'Hedefe özgü kolon korunuyor; DROP veya RENAME üretilmez.',tag='column:'+name))
            continue
        if any(diff.kind=='UNKNOWN' for diff in column_changes):
            exists_proven=(before is not None and desired.coverage.ddl==actual.coverage.ddl=='COMPLETE'
                           and _value(after,'exists') is True and _value(before,'exists') is True)
            preserve_unknown=(exists_proven
                              and all(diff.kind in {'UNKNOWN','INFORMATIONAL'} for diff in column_changes))
            if preserve_unknown:
                result.append(operation(context,desired,column_changes,'PRESERVE','INFORMATIONAL',
                                        'COLUMN_COMPARISON_INCOMPLETE_PRESERVED',
                                        'Kolon karşılaştırması eksik; bilinen dönüşüm bulunmadığından mevcut kolon korunuyor, SQL üretilmiyor.',
                                        tag='column:'+name,feature_scope='COLUMN'))
                continue
            unknown=[diff for diff in column_changes if diff.kind=='UNKNOWN']
            independent=(exists_proven
                         and all(diff.property_path.rsplit('/',1)[-1] in {'collation','length_semantics'} for diff in unknown)
                         and all(diff.kind in {'UNKNOWN','INFORMATIONAL'} or
                                 diff.property_path.rsplit('/',1)[-1] in {'default','nullable'} for diff in column_changes))
            if independent:
                result.append(operation(context,desired,unknown,'PRESERVE','INFORMATIONAL',
                                        'COLUMN_COMPARISON_INCOMPLETE_PRESERVED',
                                        'Kolonun karakter ayarları bilinmiyor; bağımsız default veya NULL koşulu ayrı değerlendirilir.',
                                        tag='column:'+name,feature_scope='COLUMN'))
                column_changes=[diff for diff in column_changes if diff.kind!='UNKNOWN']
            else:
                result.append(operation(context,desired,column_changes,'REVIEW','BLOCKED','COLUMN_METADATA_UNKNOWN',
                                        'Kolonun bilinmeyen alanları uygulanabilir dönüşüm olarak sunulamaz.',tag='column:'+name))
                continue
        if before is None:
            projection_actual=source_projection(actual)
            dictionary=actual.properties.get('dictionary.tables')
            partitioned=(bool(projection_actual and projection_actual.properties.get('table_properties',{}).get('partitioning'))
                         or bool(dictionary and dictionary.state=='KNOWN' and any(row.get('partitioned')=='YES' for row in dictionary.value)))
            if partitioned and _value(after,'data_type') in {'LONG','LONG RAW'}:
                result.append(operation(context,desired,column_changes,'REVIEW','BLOCKED','PARTITION_COLUMN_TYPE_UNSUPPORTED',
                                        'Partition tabloya LONG veya LONG RAW kolon eklenemez.',tag='column:'+name))
                continue
            projection = source_projection(desired)
            detail = projection.properties.get('columns',{}).get(name) if projection else None
            complex_column = (not detail or detail.get('identity') or detail.get('virtual_expression')
                              or any(token.upper in {'CONSTRAINT','PRIMARY','UNIQUE','CHECK','REFERENCES'}
                                     for token in code_tokens(detail.get('definition','')) or ()))
            if _value(after,'nullable') is not True or complex_column or _value(after,'default') is not None:
                result.append(operation(context,desired,column_changes,'REVIEW','REVIEW_REQUIRED','NEW_COLUMN_REQUIRES_DATA_REVIEW',
                                        'Mevcut tabloya bu kolonun eklenmesi veri/constraint etkisi incelemesi gerektiriyor.',tag='column:'+name))
            else:
                collation_enabled,capability_ids=_collation_capability(context)
                try:
                    raw = column_definition(name,detail,fields=after,collation_enabled=collation_enabled)
                except (ValueError,KeyError,TypeError,StopIteration) as error:
                    result.append(operation(context,desired,column_changes,'REVIEW','BLOCKED',_definition_error(error),
                                            'Yeni kolonun kaynak tanımı veya hedefte collation korunumu doğrulanamadı.',
                                            tag='column:'+name,extra_evidence_ids=capability_ids))
                    continue
                result.append(operation(context,desired,column_changes,'ADD_COLUMN','READY','ADD_MISSING_NULLABLE_COLUMN',
                                        'Yalnız eksik nullable kolon eklenecek; mevcut veriler taşınmayacak.',
                                        statement=f'ALTER TABLE {qualified(desired.identity)} ADD ({raw});'.encode(),
                                        phase=25,tag='column:'+name,feature_scope='COLUMN',extra_evidence_ids=capability_ids,affected_columns=(name,)))
            continue
        typed = [diff for diff in column_changes if diff.property_path.rsplit('/',1)[-1] in
                 {'data_type','length','length_semantics','precision','scale','fractional_precision'}]
        remaining = [diff for diff in column_changes if diff not in typed]
        if typed:
            old_type,new_type = _value(before,'data_type'),_value(after,'data_type')
            widening = False
            if old_type==new_type and old_type in {'VARCHAR2','NVARCHAR2','RAW'}:
                old_length,new_length = _value(before,'length'),_value(after,'length')
                semantics = _value(after,'length_semantics')
                max_bytes = context.target.capabilities.get('max_varchar2_bytes')
                factor = context.target.capabilities.get('max_bytes_per_character')
                ceiling = 2000 if old_type=='RAW' else max_bytes.value if max_bytes and max_bytes.state=='KNOWN' else None
                width = 1 if semantics=='BYTE' else 6 if old_type=='NVARCHAR2' else factor.value if factor and factor.state=='KNOWN' else None
                same_semantics=(semantics==_value(before,'length_semantics') and isinstance(old_length,int) and isinstance(new_length,int) and new_length>old_length)
                expanded_semantics=(old_type=='VARCHAR2' and _value(before,'length_semantics')=='BYTE' and semantics=='CHAR'
                                    and isinstance(old_length,int) and isinstance(new_length,int) and new_length>=old_length)
                widening = (isinstance(old_length,int) and isinstance(new_length,int) and (same_semantics or expanded_semantics)
                            and ceiling is not None and width is not None
                            and new_length*width<=ceiling)
            elif old_type==new_type=='NUMBER':
                left,right,scale = _value(before,'precision'),_value(after,'precision'),_value(after,'scale')
                widening = (isinstance(left,int) and isinstance(right,int) and 1<=left<right<=38
                            and isinstance(scale,int) and scale==_value(before,'scale'))
            if widening and _safety_proven(actual,name):
                datatype = datatype_sql(after)
                result.append(operation(context,desired,typed,'MODIFY_COLUMN','READY','SAFE_TYPE_WIDENING',
                                        'Aynı tip ve semantikte, sınırları ve bağımlılık engelleri doğrulanmış genişletme.',
                                        statement=f'ALTER TABLE {qualified(desired.identity)} MODIFY ({quote_identifier(name)} {datatype});'.encode(),
                                        phase=30,tag='type:'+name,feature_scope='COLUMN'))
            else:
                from .review_reasons import type_review
                result.append(operation(context,desired,typed,'REVIEW','REVIEW_REQUIRED' if not widening else 'BLOCKED',
                                        'TYPE_CHANGE_REQUIRES_REVIEW' if not widening else 'TYPE_SAFETY_METADATA_UNVERIFIED',
                                        type_review(name,before,after)+(' Partition anahtarı veya domain index güvenlik kanıtı eksik.' if widening else ''),tag='type:'+name))
        for diff in remaining:
            field = diff.property_path.rsplit('/',1)[-1]
            if diff.kind=='INFORMATIONAL' or field=='position':
                decision,code,description = 'INFORMATIONAL','COLUMN_ORDER_PRESERVED','Kolon sırası raporlanır; tablo yeniden oluşturulmaz.'
            elif field in {'identity','virtual_expression'}:
                decision,code,description = 'BLOCKED','EXISTING_GENERATED_COLUMN_CHANGE_UNSUPPORTED','Mevcut identity veya virtual kolon değişimi V1 kapsamında üretilemez.'
            else:
                decision,code,description = 'REVIEW_REQUIRED','COLUMN_CHANGE_REQUIRES_REVIEW','Kolon özelliği veri veya operasyon koşulu incelemesi gerektiriyor.'
            statement = None
            if field=='default' and _value(after,'default_on_null') is False and _value(before,'default_on_null') is False:
                projection = source_projection(desired)
                raw_default = projection.properties['columns'][name].get('default') if projection else None
                tokens = code_tokens(raw_default or 'NULL') or ()
                if tokens and not any(token.upper in {'SELECT','NEXTVAL','CASE'} or token.text=='(' for token in tokens):
                    decision,code,description = 'READY','SET_VERIFIED_COLUMN_DEFAULT','Yalnız gelecekteki kayıtların default tanımı değiştirilecek; backfill yok.'
                    statement = f'ALTER TABLE {qualified(desired.identity)} MODIFY ({quote_identifier(name)} DEFAULT {raw_default or "NULL"});'.encode()
            proof=()
            if field=='nullable':
                from .column_safety import not_null_relaxation_evidence
                proof=not_null_relaxation_evidence(actual,name,before,after)
                if proof:
                    decision,code,description='READY','RELAX_VERIFIED_NOT_NULL','Kaynakta nullable olan kolonun açık NOT NULL koşulu, PK olmadığı doğrulanarak gevşetilecek; veri güncellenmez.'
                    statement=f'ALTER TABLE {qualified(desired.identity)} MODIFY ({quote_identifier(name)} NULL);'.encode()
                elif _value(after,'nullable') is False:
                    description=name+': kaynak NOT NULL istiyor. Mevcut veride NULL bulunmadığı ve kısıt etkisi doğrulanmalı.'
                else:
                    description=name+': NULL kabulü isteniyor. Açık NOT NULL tanımı ve PK/kısıt envanteri birlikte doğrulanamadı.'
            elif field=='collation':
                description=name+': collation hedefte '+str(diff.before.value)+', kaynakta '+str(diff.after.value)+'. Tip/karakter karşılaştırma etkisi ayrıca incelenmeli.'
            result.append(operation(context,desired,(diff,),'MODIFY_COLUMN' if decision=='READY' else 'PRESERVE' if decision=='INFORMATIONAL' else 'REVIEW',
                                    decision,code,description,statement=statement,tag=field+':'+name,feature_scope='COLUMN',extra_evidence_ids=proof or ()))
    if other:
        partition=[diff for diff in other if diff.property_path=='/table_properties/partitioning' and diff.kind not in {'UNKNOWN','EXTRA','INFORMATIONAL'}]
        if partition:
            from .partition_rules import partition_change
            result.append(partition_change(context,desired,actual,partition))
            other=[diff for diff in other if diff not in partition]
        storage=[diff for diff in other if diff.property_path=='/table_properties/lob_storage'
                 and not context.profile.policy.compare_physical_storage and diff.kind!='UNKNOWN']
        if storage:
            result.append(operation(context,actual,storage,'PRESERVE','INFORMATIONAL','PHYSICAL_STORAGE_PRESERVED',
                                    'Mevcut LOB depolama ayarları korunacak.',tag='lob-storage'))
            other=[diff for diff in other if diff not in storage]
        unsupported=[diff for diff in other if diff.property_path.startswith('/table_properties/')
                     and diff.kind not in {'INFORMATIONAL','EXTRA'}]
        if unsupported:
            result.append(operation(context,desired,unsupported,'REVIEW','BLOCKED','TABLE_LAYOUT_CHANGE_UNSUPPORTED',
                                    'Partition veya tablo yerleşimi değişikliği için dönüşüm SQL’i üretilemiyor.',tag='layout'))
            other=[diff for diff in other if diff not in unsupported]
    constraints={}
    for diff in other:
        parts=diff.property_path.split('/')
        if len(parts)==4 and parts[1]=='constraints':
            constraints.setdefault(parts[2],[]).append(diff)
    projection=source_projection(desired)
    source_constraints=projection.properties.get('constraints',{}) if projection else {}
    for escaped_name,constraint_changes in sorted(constraints.items()):
        name=escaped_name.replace('~1','/').replace('~0','~')
        source_unknown=(not context.profile.policy.allow_drop and desired.coverage.ddl=='COMPLETE'
                        and projection is not None and name not in source_constraints
                        and all(diff.before.state=='KNOWN' and diff.after.state=='UNKNOWN'
                                for diff in constraint_changes))
        preserved=all(diff.kind in {'EXTRA','INFORMATIONAL'} for diff in constraint_changes)
        if source_unknown or preserved:
            code='TARGET_CONSTRAINT_PRESERVED_SOURCE_UNKNOWN' if source_unknown else 'TARGET_ONLY_CONSTRAINT_PRESERVED'
            result.append(operation(context,actual,constraint_changes,'PRESERVE','INFORMATIONAL',code,
                                    f'{name} hedef constraint tanımı korunuyor; kaynak yokluğu doğrulanmadı.' if source_unknown
                                    else f'{name} hedef constraint tanımı korunuyor; otomatik silme yok.',
                                    tag='constraint-change:'+name,feature_scope='CONSTRAINT'))
        else:
            result.append(operation(context,desired,constraint_changes,'REVIEW',
                                    'BLOCKED' if any(diff.kind=='UNKNOWN' for diff in constraint_changes) else 'REVIEW_REQUIRED',
                                    'TABLE_COMPONENT_CHANGE_REQUIRES_REVIEW',
                                    f'{name} constraint tanımı veri veya operasyon koşulu incelemesi gerektiriyor.',
                                    tag='constraint-change:'+name,feature_scope='CONSTRAINT'))
    constraint_change_ids={diff.difference_id for group in constraints.values() for diff in group}
    other=[diff for diff in other if diff.difference_id not in constraint_change_ids]
    if other:
        if all(diff.kind=='INFORMATIONAL' or diff.kind=='EXTRA' for diff in other):
            result.append(operation(context,actual,other,'PRESERVE','INFORMATIONAL','TARGET_ONLY_DEFINITION_PRESERVED',
                                    'Hedefe özgü tanımlar korunuyor; otomatik silme yok.',tag='other'))
        else:
            result.append(operation(context,desired,other,'REVIEW','BLOCKED' if any(diff.kind=='UNKNOWN' for diff in other) else 'REVIEW_REQUIRED',
                                    'TABLE_COMPONENT_CHANGE_REQUIRES_REVIEW','Constraint veya tablo özelliği değişimi ayrı inceleme gerektiriyor.',tag='other'))
    return result
