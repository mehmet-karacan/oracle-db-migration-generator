from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens, enclosed, identifier, source_span, top_level_items
from ..compare.projection_adapter import restore_projection
from ..parsing.adapter import parse_ddl
from ..parsing.statements import quote_identifier
import re


def qualified(identity):
    return quote_identifier(identity.owner.effective_name)+'.'+quote_identifier(identity.name.effective_name)


def source_projection(obj):
    projection = restore_projection(obj)
    if projection is None and obj.raw_ddl:
        parsed = parse_ddl(obj.raw_ddl,obj.identity)
        valid = next((item for item in parsed.objects if item.identity.key==obj.object_key and item.parse_ok and not item.diagnostics),None)
        projection = valid.projection if valid else None
    return projection


def _explicit_length_semantics(sql,fields):
    if not fields:return sql
    datatype=fields.get('data_type')
    if datatype is None or datatype.state!='KNOWN' or datatype.value not in {'VARCHAR2','CHAR'}:return sql
    semantics=fields.get('length_semantics')
    if semantics is None or semantics.state!='KNOWN' or semantics.value not in {'BYTE','CHAR'}:
        raise ValueError('SOURCE_LENGTH_SEMANTICS_UNKNOWN')
    tokens=code_tokens(sql) or ()
    spellings={'VARCHAR2','VARCHAR'} if datatype.value=='VARCHAR2' else {'CHAR'}
    if len(tokens)<2 or tokens[1].upper not in spellings:raise ValueError('COLUMN_TYPE_UNVERIFIED')
    if len(tokens)>2 and tokens[2].text=='(':
        body=enclosed(tokens,2)
        if body is None:raise ValueError('COLUMN_LENGTH_UNVERIFIED')
        explicit=[token.upper for token in body[0] if token.upper in {'BYTE','CHAR'}]
        if explicit:
            if explicit!=[semantics.value]:raise ValueError('SOURCE_LENGTH_SEMANTICS_CONFLICT')
            return sql
        end=tokens[body[1]-1].start
        return sql[:end]+' '+semantics.value+sql[end:]
    if datatype.value=='CHAR':
        # CHAR without an explicit size has Oracle's documented size 1.
        return sql[:tokens[1].end]+'(1 '+semantics.value+')'+sql[tokens[1].end:]
    raise ValueError('COLUMN_LENGTH_UNVERIFIED')


def _datatype_end(tokens):
    if len(tokens)<2:raise ValueError('COLUMN_TYPE_UNVERIFIED')
    if len(tokens)>2 and tokens[2].text=='(':
        body=enclosed(tokens,2)
        if body is None:raise ValueError('COLUMN_TYPE_UNVERIFIED')
        return body[1]
    return 2


def _explicit_collation(sql,fields,enabled):
    if not fields:return sql
    datatype,collation=fields.get('data_type'),fields.get('collation')
    if datatype is None or datatype.state!='KNOWN':return sql
    tokens=code_tokens(sql) or ()
    at=_datatype_end(tokens)
    explicit=at<len(tokens) and tokens[at].upper=='COLLATE'
    if datatype.value in {'CLOB','NCLOB'}:
        if collation and collation.state=='KNOWN' and collation.value not in {None,'USING_NLS_COMP'}:
            raise ValueError('SOURCE_COLLATION_CONFLICT')
        # Intrinsic collation needs no declaration, but explicit raw syntax
        # must pass the same target capability gate as character columns.
        if not explicit:return sql
    elif datatype.value not in {'CHAR','VARCHAR2','NCHAR','NVARCHAR2','LONG'}:
        if explicit or collation and collation.state=='KNOWN' and collation.value is not None:
            raise ValueError('SOURCE_COLLATION_CONFLICT')
        return sql
    if collation is None or collation.state!='KNOWN' or collation.value is None:
        if explicit:raise ValueError('SOURCE_COLLATION_UNVERIFIED')
        return sql
    name=str(collation.value)
    if not re.fullmatch(r'[A-Z][A-Z0-9_$#]*',name):raise ValueError('SOURCE_COLLATION_UNVERIFIED')
    if explicit and (at+1>=len(tokens) or identifier(tokens[at+1])[0]!=name):
        raise ValueError('SOURCE_COLLATION_CONFLICT')
    if enabled is None:raise ValueError('TARGET_COLLATION_CAPABILITY_UNKNOWN')
    if enabled is False:
        # With data-bound collation disabled, all user-defined object columns
        # have USING_NLS_COMP and COLLATE declarations are unavailable.
        if explicit or name!='USING_NLS_COMP':raise ValueError('TARGET_COLLATION_SYNTAX_UNAVAILABLE')
        return sql
    if explicit:return sql
    end=tokens[at-1].end
    return sql[:end]+' COLLATE '+name+sql[end:]


def column_definition(name,detail,*,reconstruct=False,fields=None,collation_enabled=None):
    if not reconstruct:
        return _explicit_collation(_explicit_length_semantics(detail['definition'],fields),fields,collation_enabled)
    if detail.get('identity') or detail.get('virtual_expression'):
        raise ValueError('COMPLEX_COLUMN_CONTEXT_NOT_EMITTABLE')
    if any(token.upper in {'CONSTRAINT','PRIMARY','UNIQUE','CHECK','REFERENCES'} for token in code_tokens(detail.get('definition','')) or ()):
        raise ValueError('INLINE_CONSTRAINT_CONTEXT_NOT_EMITTABLE')
    if not detail.get('data_type'):
        raise ValueError('COLUMN_TYPE_NOT_VERIFIED')
    sql = quote_identifier(name)+' '+detail['data_type']
    if detail.get('collation'):
        original_tokens=code_tokens(detail.get('definition','')) or ()
        at=_datatype_end(original_tokens)
        declared=at<len(original_tokens) and original_tokens[at].upper=='COLLATE'
        if fields is None or declared or collation_enabled is True:
            sql += ' COLLATE '+detail['collation']
    if detail.get('default') is not None:
        sql += ' DEFAULT'+(' ON NULL' if detail.get('default_on_null') else '')+' '+detail['default']
    if detail.get('nullable')=='NOT NULL':
        sql += ' NOT NULL'
        # Reconstructing an ALTERed column must preserve the original constraint
        # state rather than silently enabling a disabled NOT NULL declaration.
        original=code_tokens(detail.get('definition','')) or ()
        depth=0
        words=[]
        for token in original:
            if token.text=='(':depth+=1
            words.append(token.upper if depth==0 else None)
            if token.text==')':depth-=1
        at=next((i+2 for i in range(len(words)-1) if words[i:i+2]==['NOT','NULL']),None)
        if at is not None:
            stop=next((i for i in range(at,len(words)) if words[i] not in
                       {'ENABLE','DISABLE','VALIDATE','NOVALIDATE','RELY','NORELY','DEFERRABLE','NOT','INITIALLY','IMMEDIATE','DEFERRED'}),len(words))
            if stop>at:sql += ' '+source_span(detail['definition'],original[at:stop])
    if detail.get('visibility')=='INVISIBLE':
        sql += ' INVISIBLE'
    return _explicit_collation(_explicit_length_semantics(sql,fields),fields,collation_enabled)


def table_base(obj,*,columns_fields=None,collation_enabled=None):
    projection = source_projection(obj)
    if projection is None or not obj.raw_ddl:
        raise ValueError('SOURCE_DDL_NOT_AVAILABLE')
    columns = projection.properties.get('columns',{})
    if not columns:
        raise ValueError('SOURCE_TABLE_COLUMNS_UNAVAILABLE')
    # GET_DDL can append backing indexes and ALTER TABLE context without
    # terminators. Only the parser-proven CREATE span belongs to this intent.
    # Constraints and indexes retain their separate dependency-aware intents.
    parsed = parse_ddl(obj.raw_ddl, obj.identity, metadata=True)
    create = next((item for item in parsed.objects if item.identity.key == obj.object_key
                   and item.parse_ok and not item.diagnostics), None)
    if parsed.coverage != 'COMPLETE' or create is None:
        raise ValueError('SOURCE_TABLE_BODY_UNAVAILABLE')
    text = create.raw_ddl.decode('utf-8')
    tokens = code_tokens(text)
    depth=0
    for index,token in enumerate(tokens):
        if token.text=='(': depth+=1
        elif token.text==')': depth-=1
        elif depth==0 and token.upper=='AS' and (index==0 or tokens[index-1].upper!='STORE'):
            # CTAS reads business rows and can populate the new table. It is
            # outside the DDL-only plan even when its dependency is verified.
            raise ValueError('CREATE_TABLE_AS_QUERY_NOT_SUPPORTED')
    table_at = next(i for i,t in enumerate(tokens) if t.upper=='TABLE')
    opening = next(i for i in range(table_at+1,len(tokens)) if tokens[i].text=='(')
    body = enclosed(tokens,opening)
    if body is None:
        raise ValueError('SOURCE_TABLE_BODY_UNAVAILABLE')
    closing = tokens[body[1]-1]
    prefix = text[:tokens[opening].end]
    suffix = text[closing.start:].rstrip().rstrip(';')
    suffix_words=[token.upper for token in code_tokens(suffix) or ()]
    if any(suffix_words[index:index+2]==['DEFAULT','COLLATION'] for index in range(len(suffix_words)-1)):
        if collation_enabled is None:raise ValueError('TARGET_COLLATION_CAPABILITY_UNKNOWN')
        if collation_enabled is False:raise ValueError('TARGET_COLLATION_SYNTAX_UNAVAILABLE')
    changed = projection.properties.get('_context_changed_columns',())
    definitions = [column_definition(name,detail,reconstruct=name in changed,fields=(columns_fields or {}).get(name),collation_enabled=collation_enabled)
                   for name,detail in sorted(columns.items(),key=lambda pair:int(pair[1]['position']))]
    definitions.extend(item['definition'] for item in projection.properties.get('_generator_supplemental_logging',()))
    return (prefix+'\n  '+',\n  '.join(definitions)+'\n'+suffix+';').encode('utf-8')


def datatype_sql(fields):
    def known(key):
        value = fields.get(key)
        if value is None or value.state!='KNOWN':
            raise ValueError('COLUMN_TYPE_NOT_VERIFIED')
        return value.value
    datatype = known('data_type')
    if datatype in {'VARCHAR2','VARCHAR','NVARCHAR2','RAW','CHAR','NCHAR'}:
        length = known('length')
        semantics = known('length_semantics')
        if not isinstance(length,int) or length<1:
            raise ValueError('COLUMN_LENGTH_INVALID')
        suffix = ' '+semantics if datatype in {'VARCHAR2','VARCHAR','CHAR'} and semantics in {'CHAR','BYTE'} else ''
        return f'{datatype}({length}{suffix})'
    if datatype=='NUMBER':
        precision,scale = known('precision'),known('scale')
        if precision is None and scale is None:
            return 'NUMBER'
        if precision is None or scale is None:
            raise ValueError('NUMBER_PRECISION_OR_SCALE_NOT_EXPLICIT')
        return f'NUMBER({precision},{scale})'
    raise ValueError('DATATYPE_MODIFY_NOT_SUPPORTED')
