"""Typed Oracle fields plus unchanged Analyzer structured-diff adapters."""
import re
import json
from dataclasses import fields, replace

from .._vendor.analyzer_core.oracle.changes import compare_projections
from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens, identifier
from .._vendor.analyzer_core.oracle.dynamic_sql import DynamicSqlProfile
from .._vendor.analyzer_core.oracle.package import Parameter, Routine
from .._vendor.analyzer_core.oracle.projections import Projection
from .._vendor.analyzer_core.oracle.table import constraint_properties
from ..model.serialization import thaw
from ..model.identity import Identifier
from ..model.snapshot import KnownValue
from ..parsing.canonicalize import canonical_sql
from ..parsing.statements import literal_value
from ..parsing.projections import normalize_column_semantics


def pointer(value):
    return str(value).replace('~','~0').replace('/','~1')


def align_anonymous_constraints(actual,desired):
    """Only source-anonymous names may adopt an equivalent target identity.

    Reserve every source named constraint first. Match kind+columns/expression,
    retaining target state fields so disabled/novalidate differences survive.
    Ambiguous, nonidentical definitions remain visible for review.
    """
    def groups(fields):
        result={}
        for path,value in fields.items():
            parts=path.split('/')
            if len(parts)==4 and parts[1]=='constraints':
                result.setdefault(parts[2],{})[parts[3]]=value
        return result
    old,new=groups(actual),groups(desired)
    reserved=set(old)&set(new)
    result=dict(actual)
    def signature(values):
        return tuple(values.get(key).value if values.get(key) and values[key].state=='KNOWN' else None
                     for key in ('kind','columns','condition'))
    def equivalent(left,right):
        return set(left)==set(right) and all(left[key].state==right[key].state and left[key].value==right[key].value for key in left)
    for name,values in sorted(new.items()):
        if not name.startswith('@anonymous-') or name in reserved: continue
        candidates=[key for key in sorted(old) if key not in reserved and signature(old[key])==signature(values)]
        exact=[key for key in candidates if equivalent(old[key],values)]
        match=exact[0] if exact else candidates[0] if len(candidates)==1 else None
        if match is None: continue
        reserved.add(match)
        for field,value in old[match].items():
            result.pop('/constraints/'+match+'/'+field)
            result['/constraints/'+name+'/'+field]=value
    return result


def _routine(data):
    values = dict(data)
    values['parameters'] = tuple(Parameter(**item) for item in values['parameters'])
    values['dynamic_sql_profiles'] = tuple(DynamicSqlProfile(**item) for item in values['dynamic_sql_profiles'])
    for key,value in tuple(values.items()):
        if isinstance(value,list):
            values[key] = tuple(value)
    return Routine(**values)


def restore_projection(obj):
    if obj.projection is not None:
        return normalize_column_semantics(replace(obj.projection, object_key=obj.object_key))
    value = obj.properties.get('projection')
    if value is None or value.state!='KNOWN':
        return None
    properties = thaw(value.value)
    if 'routines' in properties:
        properties['routines'] = tuple(_routine(item) for item in properties['routines'])
    return normalize_column_semantics(Projection(obj.object_key,obj.identity.object_type,properties,
                      'structural' if obj.coverage.ddl=='COMPLETE' else 'text_fallback',obj.coverage.diagnostics))


def structured_changes(actual, desired):
    old, new = restore_projection(actual), restore_projection(desired)
    if old is None or new is None:
        return None
    try:
        return compare_projections(old,new,old_evidence_ids=actual.evidence_ids,new_evidence_ids=desired.evidence_ids)
    except ValueError:
        return None  # Type has an explicit Generator fallback, never NO_CHANGE.


def _default(value):
    if value is None or not str(value).strip() or str(value).strip().upper()=='NULL':
        return None
    return canonical_sql(str(value))


def _integer(value):
    return int(str(value)) if value is not None and re.fullmatch(r'[+-]?\d+',str(value)) else None


def table_columns(obj,snapshot):
    projection = restore_projection(obj)
    columns = dict(projection.properties.get('columns',{})) if projection else {}
    result = {}
    dictionary = obj.properties.get('dictionary.columns')
    metadata = {row['column_name']:row for row in dictionary.value
                if not (row.get('hidden_column')=='YES' and row.get('user_generated')=='NO')} if dictionary and dictionary.state=='KNOWN' else {}
    names = set(columns) | set(metadata)
    primary_columns = set()
    if projection:
        for definition in projection.properties.get('constraints',{}).values():
            detail = constraint_properties(definition)
            if detail.get('kind')=='PRIMARY KEY' and detail.get('columns'):
                tokens = code_tokens(detail['columns']) or ()
                primary_columns.update(identifier(token)[0] for token in tokens if token.text!=',')
    for name in sorted(names):
        item = dict(columns.get(name,{}))
        row = metadata.get(name)
        identity_conflict=(snapshot.side=='TARGET' and row is not None and row.get('identity_column') in {'YES','NO'}
                           and bool(item.get('identity'))!=(row['identity_column']=='YES'))
        tokenized = code_tokens(item.get('data_type') or '') or ()
        base_type = tokenized[0].upper if tokenized else None
        # Oracle 19c defines VARCHAR as a synonym for VARCHAR2. Keep the raw
        # source spelling for emission while comparing its actual data type.
        if base_type=='VARCHAR':base_type='VARCHAR2'
        details = {
            'exists':True, 'data_type':base_type,
            'length':_integer(item.get('length')), 'length_semantics':item.get('length_semantics'),
            'precision':_integer(item.get('precision')), 'scale':_integer(item.get('scale')),
            'nullable':item.get('nullable')!='NOT NULL' and name not in primary_columns and not bool(item.get('identity')),
            'default':_default(item.get('default')), 'default_on_null':bool(item.get('default_on_null')),
            'identity':canonical_sql(item['identity']) if item.get('identity') else None,
            'virtual_expression':canonical_sql(item['virtual_expression']) if item.get('virtual_expression') else None,
            'visibility':item.get('visibility') or 'VISIBLE', 'position':_integer(item.get('position')),
            'collation':item.get('collation'),
            'fractional_precision':None,
        }
        if base_type=='NUMBER' and details['precision'] is not None and details['scale'] is None:
            details['scale'] = 0
        if base_type in {'CHAR','NCHAR'} and len(tokenized)==1:
            details['length']=1
        if base_type in {'NVARCHAR2','NCHAR'}:
            details['length_semantics'] = 'CHAR'
        if base_type=='RAW':
            details['length_semantics'] = 'BYTE'
        if row:
            details.update(data_type=row['data_type'],
                           length=row['char_length'] if row.get('char_used')=='C' else row['data_length'] if row['data_type'] in {'CHAR','VARCHAR2','NCHAR','NVARCHAR2','RAW'} else None,
                           length_semantics='CHAR' if row.get('char_used')=='C' else 'BYTE' if row.get('char_used')=='B' or row['data_type']=='RAW' else None,
                           precision=row['data_precision'],scale=row['data_scale'],nullable=row['nullable']=='Y',
                           default=_default(row['data_default']) if row.get('virtual_column')!='YES' and row.get('identity_column')!='YES' else None,
                           default_on_null=row.get('default_on_null')=='YES' and row.get('identity_column')!='YES',
                           virtual_expression=_default(row['data_default']) if row.get('virtual_column')=='YES' else None,
                           visibility='INVISIBLE' if row.get('hidden_column')=='YES' else 'VISIBLE',
                           position=row['column_id'],collation=row.get('collation'))
            if row.get('identity_column')=='YES' and details['identity'] is None:
                details['identity'] = 'IDENTITY_METADATA_PRESENT_DEFINITION_UNRESOLVED'
            elif row.get('identity_column')=='NO' and snapshot.side=='SOURCE':
                # Do not copy source identity presence over contradictory
                # dictionary facts during source correspondence.
                details['identity'] = None
        if base_type=='TIMESTAMP' or str(details['data_type']).startswith('TIMESTAMP'):
            type_text = str(row['data_type'] if row else item.get('data_type','TIMESTAMP')).upper()
            match = re.search(r'TIMESTAMP\s*\(\s*(\d+)\s*\)',type_text)
            fractional = int(match.group(1)) if match else row.get('data_scale') if row else None
            details['fractional_precision'] = 6 if fractional is None else int(fractional)
            details['data_type'] = 'TIMESTAMP WITH LOCAL TIME ZONE' if 'LOCAL TIME ZONE' in type_text else 'TIMESTAMP WITH TIME ZONE' if 'TIME ZONE' in type_text else 'TIMESTAMP'
            details['precision'] = details['scale'] = None
        if details.get('collation'):
            details['collation'] = Identifier.parse(details['collation']).effective_name
        elif details['data_type'] in {'CLOB','NCLOB'}:
            # Oracle fixes LOB collation independently of table/schema defaults.
            # https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/CREATE-TABLE.html
            details['collation']='USING_NLS_COMP'
        ids = dictionary.evidence_ids if row and dictionary else obj.evidence_ids
        facts = {key:KnownValue('KNOWN',value,ids) for key,value in details.items()}
        if identity_conflict:
            facts['identity'] = KnownValue('UNKNOWN',None,ids)
        if details['data_type'] in {'VARCHAR2','CHAR'} and details['length_semantics'] is None:
            configured = snapshot.capabilities.get('source_length_semantics')
            if configured and configured.state=='KNOWN':
                facts['length_semantics'] = KnownValue('KNOWN',configured.value,configured.evidence_ids)
            else:
                facts['length_semantics'] = KnownValue('UNKNOWN',None,ids)
        if details['data_type'] is None:
            facts['data_type'] = KnownValue('UNKNOWN',None,ids)
        result[name] = facts
    return result


def sequence_fields(projection):
    values = projection.properties
    increment_value = _integer(values.get('increment_by'))
    increment = str(1 if increment_value is None else increment_value)
    ascending = int(increment)>0
    minimum = '1' if ascending else str(-(10**27-1))
    maximum = str(10**28-1) if ascending else '-1'
    # Oracle SQL Reference 19c, CREATE SEQUENCE: default min/max, cache and flags.
    # https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/CREATE-SEQUENCE.html
    def bound(key,default):
        raw = values.get(key)
        if raw and not raw.startswith('NO'):
            return str(int(raw.split()[-1]))
        return default
    minimum, maximum = bound('min_value',minimum), bound('max_value',maximum)
    cache = values.get('cache')
    start = _integer(values.get('start_with'))
    return {'increment_by':increment,'min_value':minimum,'max_value':maximum,
            'start_with':str((minimum if ascending else maximum) if start is None else start),
            'cache':'0' if cache=='NOCACHE' else str(int(cache.split()[-1])) if cache else '20',
            'cycle':values.get('cycle') or 'NOCYCLE','order':values.get('order') or 'NOORDER',
            'scale':values.get('scale') or 'NOSCALE','shard':values.get('shard') or 'NOSHARD',
            'extend':values.get('extend'),'session':values.get('session') or 'GLOBAL','keep':values.get('keep') or 'NOKEEP'}


def routine_definition(obj,snapshot):
    value = obj.properties.get('definition')
    if value is None or value.state!='KNOWN':
        return value, None
    if obj.identity.object_type not in {'PACKAGE_SPEC','PACKAGE_BODY','TYPE_SPEC','TYPE_BODY','VIEW','TRIGGER','PROCEDURE','FUNCTION','SYNONYM'}:
        return value,None
    tokens = json.loads(value.value)
    keyword = obj.identity.object_type.split('_')[0]
    boundary = next((i for i,item in enumerate(tokens) if item==['code',keyword]),None)
    if boundary is None:
        return value,None
    modifiers = {item[1] for item in tokens[1:boundary] if item[0]=='code'}
    editionable = False if 'NONEDITIONABLE' in modifiers else True if 'EDITIONABLE' in modifiers else None
    evidence_ids = value.evidence_ids
    if editionable is None and obj.identity.object_type in {'PACKAGE_BODY','TYPE_BODY'}:
        spec_kind = obj.identity.object_type.replace('_BODY','_SPEC')
        spec = next((other for other in snapshot.objects if other.identity.owner==obj.identity.owner
                     and other.identity.name==obj.identity.name and other.identity.object_type==spec_kind),None)
        if spec is not None:
            _, inherited = routine_definition(spec,snapshot)
            if inherited and inherited.state=='KNOWN':
                editionable,evidence_ids = inherited.value,inherited.evidence_ids
    elif editionable is None:
        editionable = True  # Documented default for standalone editionable types.
    ignored = {'EDITIONABLE','NONEDITIONABLE'}
    if keyword=='VIEW':
        ignored |= {'FORCE','NOFORCE'}
    normalized = [item for index,item in enumerate(tokens) if not (1<=index<boundary and item[0]=='code' and item[1] in ignored)]
    return (KnownValue('KNOWN',json.dumps(normalized,ensure_ascii=False,separators=(',',':')),value.evidence_ids),
            KnownValue('UNKNOWN' if editionable is None else 'KNOWN',editionable,evidence_ids))


def canonical_fields(obj,snapshot,policy):
    fields = {}
    projection = restore_projection(obj)
    kind = obj.identity.object_type
    def known(path,value,ids=None):
        fields[path] = KnownValue('KNOWN',value,ids or obj.evidence_ids)
    if kind=='TABLE':
        # Dictionary column facts remain independent evidence when the DDL
        # projection is unavailable. Definition/layout coverage stays unknown.
        for name,properties in table_columns(obj,snapshot).items():
            fields.update({f'/columns/{pointer(name)}/{key}':value for key,value in properties.items()})
    if kind=='TABLE' and projection:
        for name,definition in projection.properties.get('constraints',{}).items():
            known('/constraints/'+pointer(name)+'/exists',True)
            for key,value in constraint_properties(definition).items():
                if key=='index_association' and not policy.compare_physical_storage:
                    continue
                if value is None:
                    value = {'enabled':'ENABLE','validation':'VALIDATE','deferrable':'NOT DEFERRABLE',
                             'initially':'IMMEDIATE','rely':'NORELY','delete_rule':'NO ACTION'}.get(key)
                known('/constraints/'+pointer(name)+'/'+key,canonical_sql(value) if value is not None else None)
        physical = {'tablespace','storage','logging','parallel','compression','supplemental_logging'}
        for key,value in projection.properties.get('table_properties',{}).items():
            if key in physical and not policy.compare_physical_storage:
                continue
            known('/table_properties/'+pointer(key),canonical_sql(value) if value else None)
    elif kind=='SEQUENCE' and projection:
        for key,value in sequence_fields(projection).items():
            known('/sequence/'+key,value)
    elif kind=='INDEX' and projection:
        values = projection.properties
        for key in ('target','unique','kind','keys','directions','visibility'):
            value = values.get(key)
            if key=='visibility' and value is None:
                value = 'VISIBLE'
            if isinstance(value,str):
                value = canonical_sql(value)
            elif isinstance(value,(tuple,list)):
                value = [canonical_sql(item) if isinstance(item,str) else item for item in value]
            known('/index/'+key,value)
        if policy.compare_physical_storage:
            for key,value in values.get('index_properties',{}).items():
                known('/index/'+pointer(key),canonical_sql(value) if value else None)
        availability=values.get('availability','VALID')
        observed=obj.properties.get('dictionary.indexes')
        if snapshot.side=='TARGET' and observed:
            rows=observed.value if observed.state=='KNOWN' else ()
            row=next((item for item in rows if item.get('index_name')==obj.identity.name.effective_name),None)
            availability=row.get('status') if row else None
            if availability not in {'VALID','UNUSABLE'}:
                fields['/index/availability']=KnownValue('UNKNOWN',None,observed.evidence_ids)
            else: known('/index/availability',availability,observed.evidence_ids)
        else: known('/index/availability',availability)
    elif kind in {'COMMENT','GRANT'}:
        for key,value in obj.properties.items():
            if key!='definition' and not key.startswith('dictionary.'):
                fields['/'+pointer(key)] = value
    else:
        value, editionable = routine_definition(obj,snapshot)
        if value:
            fields['/definition'] = value
        if editionable is not None:
            fields['/editionable'] = editionable
        if kind=='TRIGGER' and projection:
            state=projection.properties.get('enabled_state')
            known('/trigger/enabled',state not in {'DISABLE','DISABLED'})
    # Supplied V1 snapshots also permit explicit flattened KnownValue fields.
    for key,value in obj.properties.items():
        if key not in {'projection','definition','object_status','dependencies','used_by'} and not key.startswith('dictionary.'):
            if kind not in {'COMMENT','GRANT'}:
                path = key if key.startswith('/') else '/' + '/'.join(pointer(part) for part in key.split('.'))
                if kind=='TABLE' and not key.startswith('/') and '.' in key:
                    path='/columns'+path
                fields[path] = value
    if obj.coverage.ddl!='COMPLETE':
        fields['/coverage/ddl'] = KnownValue('UNKNOWN',None,obj.evidence_ids)
    if not fields:
        fields['/definition'] = KnownValue('UNKNOWN',None,obj.evidence_ids)
    return fields
