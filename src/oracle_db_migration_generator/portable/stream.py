"""Bounded, data-only reader for the SQL*Plus portable transport."""
import base64
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re

from ..oracle.queries import CAPTURE_QUERIES, DDL_TYPES
from .builder import query_contract
from .selection import CaptureFilter

MAX_PACKET_BYTES = 64 * 1024 * 1024
INVENTORY_COLUMNS = ('object_type','object_name','status','last_ddl_time')
EXTRA_COLUMNS = {'inventory_before':INVENTORY_COLUMNS,'inventory_after':INVENTORY_COLUMNS,
                 'owner_probe':('username',),'catalog_roles':('role',),
                 'collation_parameters':('name','value'),
                 'session_calendar':('parameter','value'),
                 'dependency_objects':('owner','object_name','object_type','status'),
                 'trigger_parents':('trigger_name','table_owner','table_name')}


def _fail(code):raise ValueError('CAPTURE_'+code)


def _keys(value, required, optional=()):
    if not isinstance(value,dict) or set(value)-set(required)-set(optional) or set(required)-set(value):_fail('RECORD_SHAPE')


def _pairs(pairs):
    result={}
    for key,value in pairs:
        if key in result:_fail('DUPLICATE_JSON_KEY')
        result[key]=value
    return result


def _json(raw):
    try:return json.loads(raw,object_pairs_hook=_pairs,parse_constant=lambda _: _fail('JSON_NUMBER'))
    except (UnicodeError,json.JSONDecodeError,RecursionError):_fail('JSON_INVALID')


def _integer(value, minimum=0):
    if type(value) is not int or value<minimum:_fail('INTEGER_INVALID')
    return value


def _name(value):
    if not isinstance(value,str) or not value or ',' in value or len(value.encode('utf-8'))>128 or any(ord(c)<32 for c in value):_fail('IDENTIFIER_INVALID')
    return value


def _b64(value):
    try:
        if not isinstance(value,str):_fail('BASE64_INVALID')
        return base64.b64decode(value,validate=True)
    except (ValueError,UnicodeError):_fail('BASE64_INVALID')


def _value(value):
    if value is None:return None
    if not isinstance(value,dict):_fail('VALUE_INVALID')
    if set(value)=={'number'}:
        text=value['number']
        if not isinstance(text,str) or len(text)>80 or not re.fullmatch(r'-?\d+(?:\.\d+)?(?:[Ee][+-]?\d+)?',text):_fail('NUMBER_INVALID')
        try:number=Decimal(text)
        except InvalidOperation:_fail('NUMBER_INVALID')
        # Dictionary metadata is integral. Do not silently round decimals to floats.
        if not number.is_finite() or number.adjusted()>125 or number!=number.to_integral_value():_fail('NUMBER_NOT_INTEGRAL')
        return int(number)
    _keys(value,('encoding','chunks'))
    if value['encoding']!='base64-utf8' or not isinstance(value['chunks'],list) or len(value['chunks'])>1024:_fail('VALUE_ENCODING')
    data=bytearray()
    for chunk in value['chunks']:
        data.extend(_b64(chunk))
        if len(data)>2*1024*1024:_fail('VALUE_LIMIT')
    try:return data.decode('utf-8')
    except UnicodeError:_fail('UTF8_INVALID')


def _messages(data):
    if not isinstance(data,bytes) or not data or len(data)>MAX_PACKET_BYTES:_fail('FILE_SIZE')
    number=1;parts=0;payload=bytearray()
    for line in data.splitlines():
        if not line.strip():continue
        if len(line)>32767 or not line.isascii():_fail('TRANSPORT_LINE')
        record=_json(line)
        if not isinstance(record,dict):_fail('TRANSPORT_SHAPE')
        if record.get('record')=='capture_error':_fail('COLLECTION_FAILED')
        if record.get('record')=='chunk':
            _keys(record,('record','message','part','sha256','data'))
            if _integer(record['message'],1)!=number or _integer(record['part'])!=parts:_fail('PART_SEQUENCE')
            raw=_b64(record['data'])
            if not raw or len(raw)>16000 or not isinstance(record['sha256'],str) or hashlib.sha256(raw).hexdigest()!=record['sha256'].lower():_fail('PART_HASH')
            payload.extend(raw);parts+=1
            if len(payload)>8*1024*1024:_fail('MESSAGE_LIMIT')
        elif record.get('record')=='end_message':
            _keys(record,('record','message','parts'))
            if _integer(record['message'],1)!=number or _integer(record['parts'],1)!=parts:_fail('MESSAGE_SEQUENCE')
            yield _json(bytes(payload))
            number+=1;parts=0;payload.clear()
        else:_fail('TRANSPORT_RECORD')
    if parts or payload:_fail('TRUNCATED')


@dataclass(frozen=True,slots=True)
class CapturedQuery:
    columns:tuple
    rows:tuple | None
    error_code:str | None = None


@dataclass(frozen=True,slots=True)
class CapturedSchema:
    name:str
    authority:str
    queries:dict
    roots:tuple
    selected:tuple
    inventory_complete:bool


@dataclass(frozen=True,slots=True)
class PortableCapture:
    sha256:str
    header:dict
    selection:CaptureFilter
    schemas:dict
    status:str


def read_capture(data):
    """Validate all records before exposing any snapshot to the comparison engine."""
    header=None;scope=None;footer=None;schemas={};current=None;queries={};active=None
    columns=None;rows=[];roots=None;chosen=None;authority=None;errors=0;objects=0;count=0
    for record in _messages(data):
        count+=1
        if footer is not None or not isinstance(record,dict):_fail('RECORD_ORDER')
        kind=record.get('kind')
        if header is None:
            _keys(record,('kind','schema_version','collector_version','query_contract','session_user','database_version','captured_at','environment','selection'))
            if kind!='header' or record['schema_version']!='portable-capture/1.0' or record['collector_version']!='1.0' or record['query_contract']!=query_contract():_fail('CONTRACT_MISMATCH')
            _name(record['session_user'])
            if not isinstance(record['database_version'],str) or not re.fullmatch(r'(?:19|2[0-9])\.\d+(?:\.\d+)*',record['database_version']):_fail('DATABASE_VERSION')
            try:
                date=datetime.fromisoformat(record['captured_at'])
                if date.tzinfo is None:_fail('CAPTURE_DATE')
            except (TypeError,ValueError):_fail('CAPTURE_DATE')
            selection=record['selection'];_keys(selection,('schemas','object_types','object_names','data_types','include_related','exclude_system_generated'),('filter_side',))
            values={}
            for key in ('schemas','object_types','object_names','data_types'):
                text=selection[key]
                if text is not None and not isinstance(text,str):_fail('SELECTION_SHAPE')
                items=text.split(',') if text else []
                values[key]=['"'+_name(v).replace('"','""')+'"' for v in items] if key in {'schemas','object_names'} else items
            values.update({k:selection[k] for k in ('include_related','exclude_system_generated')})
            values['filter_side']=selection.get('filter_side','SOURCE')
            values['environment']=record['environment'] or ''
            scope=CaptureFilter.from_dict(values);header=record
            continue
        if kind=='footer':
            _keys(record,('kind','status','messages','objects','errors'))
            if current is not None or active or not schemas or record['messages']!=count or record['objects']!=objects or record['errors']!=errors or record['status']!=('PARTIAL' if errors else 'COMPLETE'):_fail('FOOTER_INVALID')
            expected=set(scope.schemas) if scope.schemas else {header['session_user']}
            if set(schemas)!=expected:_fail('SCHEMAS_INCOMPLETE')
            footer=record;continue
        owner=_name(record.get('schema'))
        if current is None:
            if owner in schemas:_fail('DUPLICATE_SCHEMA')
            current=owner;queries={};roots=None;chosen=None;authority=None
        if owner!=current:_fail('SCHEMA_ORDER')
        if kind=='schema_start':
            _keys(record,('kind','schema','authority'))
            if authority is not None or active or record['authority'] not in {'OWN','CATALOG','VISIBLE'}:_fail('AUTHORITY_INVALID')
            authority=record['authority']
            if authority=='OWN' and owner!=header['session_user']:_fail('OWNER_UNVERIFIED')
            if authority=='CATALOG' and (queries.get('catalog_roles',CapturedQuery((),None)).rows!=(('SELECT_CATALOG_ROLE',),) or queries.get('owner_probe',CapturedQuery((),None)).rows!=((owner,),)):_fail('CATALOG_UNVERIFIED')
        elif kind=='query_start':
            _keys(record,('kind','schema','query','columns'))
            name=record['query']
            if not isinstance(name,str) or active or name in queries:_fail('QUERY_ORDER')
            if authority is None and name not in {'owner_probe','catalog_roles'}:_fail('SCHEMA_START_REQUIRED')
            expected=CAPTURE_QUERIES[name][0] if name in CAPTURE_QUERIES else EXTRA_COLUMNS.get(name)
            if name.startswith('ddl:'):
                _,oracle_kind,object_name=name.split(':',2) if name.count(':')>=2 else ('','','')
                if oracle_kind not in DDL_TYPES:_fail('DDL_TYPE_INVALID')
                _name(object_name);expected=('ddl',)
            if expected is None or not isinstance(record['columns'],list) or tuple(record['columns'])!=tuple(expected):_fail('QUERY_CONTRACT')
            active=name;columns=tuple(expected);rows=[]
        elif kind=='row':
            _keys(record,('kind','schema','query','index','values'))
            if not active or record['query']!=active or _integer(record['index'])!=len(rows) or not isinstance(record['values'],list) or len(record['values'])!=len(columns):_fail('ROW_ORDER')
            rows.append(tuple(_value(v) for v in record['values']))
            if len(rows)>200000:_fail('ROW_LIMIT')
        elif kind=='query_end':
            _keys(record,('kind','schema','query','rows','status'),('error_code',))
            if not active or record['query']!=active or _integer(record['rows'])!=len(rows) or record['status'] not in {'COMPLETE','ERROR'}:_fail('QUERY_END')
            error=record.get('error_code')
            if record['status']=='ERROR':
                if not isinstance(error,str) or not re.fullmatch(r'ORA-\d{5}',error):_fail('ERROR_CODE')
                errors+=1
            elif error is not None:_fail('ERROR_CODE')
            queries[active]=CapturedQuery(columns,tuple(rows) if not error else None,error);active=None
        elif kind=='selection':
            _keys(record,('kind','schema','roots','objects'))
            if roots is not None or active or authority is None:_fail('SELECTION_ORDER')
            def identities(items):
                if not isinstance(items,list) or len(items)>100000:_fail('SELECTION_LIMIT')
                result=[]
                for item in items:
                    _keys(item,('object_type','name'))
                    if item['object_type'] not in set(DDL_TYPES.values()):_fail('SELECTION_TYPE')
                    result.append((item['object_type'],_name(item['name'])))
                if len(result)!=len(set(result)):_fail('SELECTION_DUPLICATE')
                return tuple(result)
            roots=identities(record['roots']);chosen=identities(record['objects'])
            if set(roots)-set(chosen):_fail('SELECTION_ROOT_MISSING')
        elif kind=='schema_end':
            _keys(record,('kind','schema','authority','inventory_complete','stable'))
            if active or roots is None or record['authority']!=authority or type(record['inventory_complete']) is not bool or record['inventory_complete']!=(authority in {'OWN','CATALOG'}):_fail('SCHEMA_END')
            before=queries.get('inventory_before');after=queries.get('inventory_after')
            if record['stable'] is not True or before is None or after is None or before.rows is None or before.rows!=after.rows:_fail('INVENTORY_UNSTABLE')
            inventory=set()
            for row in before.rows:
                if not all(isinstance(v,str) for v in row):_fail('INVENTORY_SHAPE')
                _name(row[1]);key=(DDL_TYPES.get(row[0],row[0].replace(' ','_')),row[1])
                if key in inventory:_fail('INVENTORY_DUPLICATE')
                inventory.add(key)
            if set(chosen)-inventory:_fail('SELECTION_INVENTORY')
            expected_ddl={'ddl:'+k+':'+n for k,n,*_ in before.rows if (DDL_TYPES.get(k),n) in chosen}
            if {k for k in queries if k.startswith('ddl:')}!=expected_ddl:_fail('DDL_INCOMPLETE')
            # An omitted dictionary group is unknown, never an empty list.
            for name,(cols,_) in CAPTURE_QUERIES.items():
                if name not in queries:queries[name]=CapturedQuery(tuple(cols),None,'CAPTURE_QUERY_MISSING')
            objects+=len(chosen)
            schemas[owner]=CapturedSchema(owner,authority,queries,roots,chosen,record['inventory_complete'])
            current=None;queries={}
        else:_fail('UNKNOWN_RECORD')
    if footer is None:_fail('FOOTER_MISSING')
    return PortableCapture(hashlib.sha256(data).hexdigest(),header,scope,schemas,footer['status'])
