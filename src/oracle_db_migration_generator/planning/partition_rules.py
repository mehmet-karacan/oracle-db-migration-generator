"""Typed proof for ordinary RANGE/INTERVAL layouts; never reconstruct the suffix."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal,InvalidOperation
import re

from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens,enclosed,identifier,top_level_items


@dataclass(frozen=True)
class RangePartition:
    name: str
    high: tuple
    options: tuple = ()


@dataclass(frozen=True)
class RangeLayout:
    keys: tuple[str,...]
    interval: tuple | None
    partitions: tuple[RangePartition,...]
    options: tuple = ()


def _logical_options(tokens):
    """Ignore only closed physical clauses; preserve all remaining semantics."""
    result=[];at=0
    while at<len(tokens):
        word=tokens[at].upper
        if word=='STORAGE' and at+1<len(tokens):
            body=enclosed(tokens,at+1)
            if body:at=body[1];continue
        if word in {'PCTFREE','PCTUSED','INITRANS','MAXTRANS','TABLESPACE'} and at+1<len(tokens):
            at+=2;continue
        if word=='SEGMENT' and at+2<len(tokens) and tokens[at+1].upper=='CREATION' and tokens[at+2].upper in {'IMMEDIATE','DEFERRED'}:
            at+=3;continue
        if word in {'LOGGING','NOLOGGING','NOCOMPRESS'} or word=='COMPRESS' and (at+1==len(tokens) or tokens[at+1].upper!='FOR'):
            at+=1;continue
        if tokens[at].text!=';':result.append(tokens[at].text if tokens[at].text.startswith(('"',"'")) else word)
        at+=1
    return tuple(result)


def _name(token):
    if not (token.text.startswith('"') and token.text.endswith('"') or re.fullmatch(r'[A-Za-z][A-Za-z0-9_$#]*',token.text)):
        raise ValueError('PARTITION_IDENTIFIER_UNVERIFIED')
    return identifier(token)[0]


def _literal(token):
    if not re.fullmatch(r"'(?:[^']|'')*'",token.text):raise ValueError('PARTITION_LITERAL_UNVERIFIED')
    return token.text[1:-1].replace("''", "'")


def _numeric(tokens):
    raw=''.join(t.text for t in tokens)
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?',raw):
        raise ValueError('PARTITION_NUMBER_UNVERIFIED')
    try:value=Decimal(raw)
    except InvalidOperation:raise ValueError('PARTITION_NUMBER_UNVERIFIED') from None
    digits=''.join(str(digit) for digit in value.as_tuple().digits).rstrip('0')
    if value and (not -130<=value.adjusted()<=125 or len(digits)>38):
        raise ValueError('PARTITION_NUMBER_NOT_REPRESENTABLE')
    return value


def _date(tokens):
    if len(tokens)==2 and tokens[0].upper in {'DATE','TIMESTAMP'}:
        text=_literal(tokens[1]).strip()
        pattern=(r'\d{4}-\d{2}-\d{2}' if tokens[0].upper=='DATE' else
                 r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{1,6})?')
    elif len(tokens)>3 and tokens[0].upper in {'TO_DATE','TO_TIMESTAMP'} and tokens[1].text=='(':
        group=enclosed(tokens,1)
        args=top_level_items(group[0]) if group and group[1]==len(tokens) else ()
        if len(args) not in {2,3} or any(len(arg)!=1 for arg in args):raise ValueError('PARTITION_DATE_UNVERIFIED')
        fmt=_literal(args[1][0]).upper()
        if fmt not in {'YYYY-MM-DD','SYYYY-MM-DD','YYYY-MM-DD HH24:MI:SS','SYYYY-MM-DD HH24:MI:SS'}:
            raise ValueError('PARTITION_DATE_FORMAT_UNVERIFIED')
        # Numeric formats do not depend on a language, but calendar must be fixed.
        if len(args)!=3 or _literal(args[2][0]).upper().replace(' ','')!='NLS_CALENDAR=GREGORIAN':
            raise ValueError('PARTITION_CALENDAR_UNVERIFIED')
        text=_literal(args[0][0]).strip()
        pattern=r'\d{4}-\d{2}-\d{2}'+(r' \d{2}:\d{2}:\d{2}' if 'HH24' in fmt else '')
    else:raise ValueError('PARTITION_DATE_UNVERIFIED')
    if not re.fullmatch(pattern,text):
        raise ValueError('PARTITION_DATE_UNVERIFIED')
    try:return datetime.fromisoformat(text)
    except ValueError:raise ValueError('PARTITION_DATE_UNVERIFIED') from None


def _bound(tokens,datatype):
    if len(tokens)==1 and tokens[0].upper=='MAXVALUE':return (1,None)
    if datatype in {'NUMBER','FLOAT'}:return (0,_numeric(tokens))
    if datatype in {'DATE','TIMESTAMP'}:return (0,_date(tokens))
    raise ValueError('PARTITION_KEY_TYPE_UNSUPPORTED')


def _interval(tokens,datatype):
    if datatype in {'NUMBER','FLOAT'}:
        size=_numeric(tokens)
        if size<=0:raise ValueError('PARTITION_INTERVAL_NONPOSITIVE')
        return ('NUMBER',size)
    if datatype not in {'DATE','TIMESTAMP'} or len(tokens)<4 or tokens[0].upper not in {'NUMTOYMINTERVAL','NUMTODSINTERVAL'}:
        raise ValueError('PARTITION_INTERVAL_UNVERIFIED')
    group=enclosed(tokens,1)
    args=top_level_items(group[0]) if group and group[1]==len(tokens) else ()
    if len(args)!=2 or len(args[1])!=1:raise ValueError('PARTITION_INTERVAL_UNVERIFIED')
    size=_numeric(args[0]);unit=_literal(args[1][0]).upper()
    allowed={'NUMTOYMINTERVAL':{'MONTH','YEAR'},'NUMTODSINTERVAL':{'DAY','HOUR','MINUTE','SECOND'}}
    if size<=0 or size>999999999 or unit not in allowed[tokens[0].upper] or size!=size.to_integral_value():
        raise ValueError('PARTITION_INTERVAL_UNVERIFIED')
    return (tokens[0].upper,size,unit)


def range_layout(obj,columns):
    """None for a heap; a closed, ordered range layout otherwise, or fail."""
    text=obj.raw_ddl.decode('utf8') if obj.raw_ddl else ''
    tokens=code_tokens(text) or ()
    table_at=next((i for i,t in enumerate(tokens) if t.upper=='TABLE'),None)
    opening=next((i for i in range((table_at or 0)+1,len(tokens)) if tokens[i].text=='('),None)
    body=enclosed(tokens,opening) if opening is not None else None
    if body is None:raise ValueError('PARTITION_TABLE_BODY_UNVERIFIED')
    positions=[i for i in range(body[1],len(tokens)-1) if tokens[i].upper=='PARTITION' and tokens[i+1].upper=='BY']
    if not positions:return None
    if len(positions)!=1:raise ValueError('PARTITION_LAYOUT_UNVERIFIED')
    at=positions[0]+2
    if tokens[at].upper!='RANGE':raise ValueError('PARTITION_METHOD_UNSUPPORTED')
    group=enclosed(tokens,at+1)
    if not group:raise ValueError('PARTITION_KEYS_UNVERIFIED')
    items=top_level_items(group[0]) or ()
    if not items or any(len(item)!=1 for item in items):raise ValueError('PARTITION_KEYS_UNVERIFIED')
    keys=tuple(_name(item[0]) for item in items)
    if len(set(keys))!=len(keys):raise ValueError('PARTITION_KEYS_UNVERIFIED')
    types=[]
    for key in keys:
        fields=columns.get(key,{})
        datatype=fields.get('data_type')
        if not datatype or datatype.state!='KNOWN' or datatype.value not in {'NUMBER','FLOAT','DATE','TIMESTAMP'}:
            raise ValueError('PARTITION_KEY_TYPE_UNSUPPORTED')
        types.append(datatype.value)
    if any(fields.get('data_type') and fields['data_type'].value in {'LONG','LONG RAW'} for fields in columns.values()):
        raise ValueError('PARTITION_COLUMN_TYPE_UNSUPPORTED')
    at=group[1];interval=None
    if tokens[at].upper=='INTERVAL':
        group=enclosed(tokens,at+1)
        if not group or len(keys)!=1:raise ValueError('PARTITION_INTERVAL_UNVERIFIED')
        interval=_interval(group[0],types[0]);at=group[1]
    group=enclosed(tokens,at)
    if not group:raise ValueError('PARTITION_LAYOUT_UNVERIFIED')
    partitions=[]
    for item in top_level_items(group[0]) or ():
        if len(item)<7 or item[0].upper!='PARTITION' or [t.upper for t in item[2:5]]!=['VALUES','LESS','THAN']:
            raise ValueError('PARTITION_BOUND_UNVERIFIED')
        name=_name(item[1]);bounds=enclosed(item,5)
        values=top_level_items(bounds[0]) if bounds else ()
        if len(values)!=len(keys):raise ValueError('PARTITION_BOUND_ARITY')
        high=tuple(_bound(value,datatype) for value,datatype in zip(values,types))
        if interval and any(value[0] for value in high):raise ValueError('PARTITION_INTERVAL_MAXVALUE')
        if partitions and (name in {p.name for p in partitions} or high<=partitions[-1].high):
            raise ValueError('PARTITION_BOUND_ORDER_OR_NAME')
        # Grammar validates the preserved physical attributes; composite partitioning
        # needs its own typed proof and cannot hide after a valid outer range.
        if any(t.upper=='SUBPARTITION' for t in item[bounds[1]:]):raise ValueError('SUBPARTITION_UNSUPPORTED')
        partitions.append(RangePartition(name,high,_logical_options(item[bounds[1]:])))
    if not partitions:raise ValueError('PARTITION_BOUNDS_EMPTY')
    return RangeLayout(keys,interval,tuple(partitions),_logical_options(tokens[group[1]:]))


def partition_change(context,desired,actual,changes):
    from .table_rules import column_fields
    from .builder import operation
    for obj in (desired,actual):
        prop=obj.properties.get('projection')
        if obj.coverage.ddl!='COMPLETE' or not prop or prop.state!='KNOWN':
            return operation(context,desired,changes,'REVIEW','BLOCKED','PARTITION_LAYOUT_UNVERIFIED',
                             'Partition yapısı için tam kaynak ve hedef kanıtı gerekli.',tag='layout')
    try:
        wanted=range_layout(desired,column_fields(desired,context.source,context.profile.policy))
        observed=range_layout(actual,column_fields(actual,context.target,context.profile.policy))
    except (ValueError,IndexError,TypeError):
        return operation(context,desired,changes,'REVIEW','BLOCKED','PARTITION_LAYOUT_UNVERIFIED',
                         'Partition key, sınır veya interval kanıtı doğrulanamadı.',tag='layout')
    if wanted is not None and wanted==observed and not context.profile.policy.compare_physical_storage:
        return operation(context,actual,changes,'PRESERVE','INFORMATIONAL','PARTITION_PHYSICAL_STORAGE_PRESERVED',
                         'Partition kolonları, adları, sınırları ve interval aynı; hedef fiziksel ayarları korunacak.',tag='layout')
    return operation(context,desired,changes,'REVIEW','REVIEW_REQUIRED','PARTITION_LAYOUT_REQUIRES_REVIEW',
                     'Partition kolon, ad, sınır veya interval farkı var; mevcut veriyi taşıyan dönüşüm DBA incelemesi gerektiriyor.',tag='layout')
