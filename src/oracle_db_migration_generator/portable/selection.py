"""One closed filter contract shared by the UI, SQL requests and comparisons."""
from dataclasses import asdict,dataclass
import re
from ..model.identity import Identifier

OBJECT_TYPES=('TABLE','INDEX','SEQUENCE','VIEW','PACKAGE_SPEC','PACKAGE_BODY','PROCEDURE','FUNCTION','TRIGGER','TYPE_SPEC','TYPE_BODY','SYNONYM','COMMENT','GRANT','MATERIALIZED_VIEW','MATERIALIZED_VIEW_LOG')


def _items(value,*,identifiers=False,data_types=False):
    if not isinstance(value,(list,tuple)) or len(value)>100:raise ValueError('CAPTURE_FILTER_LIST_INVALID')
    result=[]
    for raw in value:
        if not isinstance(raw,str) or not raw.strip():raise ValueError('CAPTURE_FILTER_VALUE_INVALID')
        text=Identifier.parse(raw.strip()).effective_name if identifiers else raw.strip().upper() if data_types else raw.strip().upper().replace(' ','_')
        if len(text.encode('utf-8'))>128 or ',' in text or any(ord(c)<32 for c in text):raise ValueError('CAPTURE_FILTER_VALUE_INVALID')
        if text not in result:result.append(text)
    return tuple(sorted(result))


@dataclass(frozen=True,slots=True)
class CaptureFilter:
    schemas:tuple[str,...]=()
    object_types:tuple[str,...]=tuple(t for t in OBJECT_TYPES if t!='GRANT')
    object_names:tuple[str,...]=()
    data_types:tuple[str,...]=()
    include_related:bool=True
    exclude_system_generated:bool=True
    environment:str=''
    reader_mode:str='AUTO'
    filter_side:str='SOURCE'
    timeout_seconds:int=900
    max_objects:int=10000

    @classmethod
    def from_dict(cls,data):
        if not isinstance(data,dict) or set(data)-set(cls.__dataclass_fields__)-{'table_names'}:raise ValueError('CAPTURE_FILTER_KEYS_INVALID')
        data=dict(data)
        tables=data.pop('table_names',[])
        if tables:
            if data.get('object_names') or data.get('object_types') and set(data['object_types'])!={'TABLE'}:raise ValueError('CAPTURE_TABLE_FILTER_CONFLICT')
            data['object_types']=['TABLE'];data['object_names']=tables
        if data.get('data_types') and not data.get('object_types'):data['object_types']=['TABLE','VIEW','MATERIALIZED_VIEW']
        for key in ('schemas','object_names'):
            if key in data:data[key]=_items(data[key],identifiers=True)
        for key in ('object_types','data_types'):
            if key in data:data[key]=_items(data[key],data_types=key=='data_types')
        value=cls(**data)
        if any(len(value.csv(key).encode('utf-8'))>4000 for key in ('schemas','object_types','object_names','data_types')):raise ValueError('CAPTURE_FILTER_BYTE_LIMIT')
        if len(value.schemas)>20 or not value.object_types or set(value.object_types)-set(OBJECT_TYPES):raise ValueError('CAPTURE_OBJECT_TYPES_INVALID')
        if value.data_types and set(value.object_types)-{'TABLE','VIEW','MATERIALIZED_VIEW'}:raise ValueError('CAPTURE_DATA_TYPE_SCOPE_INVALID')
        if any(not re.fullmatch('[A-Z][A-Z0-9_$# ]{0,127}',s) for s in value.data_types):raise ValueError('CAPTURE_DATA_TYPE_INVALID')
        if any(type(getattr(value,key)) is not bool for key in ('include_related','exclude_system_generated')):raise ValueError('CAPTURE_BOOLEAN_INVALID')
        if value.reader_mode not in {'AUTO','OWN','CATALOG','VISIBLE'}:raise ValueError('CAPTURE_READER_MODE_INVALID')
        if value.filter_side not in {'SOURCE','TARGET'}:raise ValueError('CAPTURE_FILTER_SIDE_INVALID')
        if type(value.timeout_seconds) is not int or not 30<=value.timeout_seconds<=7200:raise ValueError('CAPTURE_TIMEOUT_INVALID')
        if type(value.max_objects) is not int or not 1<=value.max_objects<=100000:raise ValueError('CAPTURE_OBJECT_LIMIT_INVALID')
        if not isinstance(value.environment,str) or len(value.environment)>80 or any(ord(c)<32 for c in value.environment):raise ValueError('CAPTURE_ENVIRONMENT_INVALID')
        return value

    def to_dict(self):
        def external(value):
            return value if re.fullmatch('[A-Z][A-Z0-9_$#]*',value) else '"'+value.replace('"','""')+'"'
        return {key:[external(v) if key in {'schemas','object_names'} else v for v in value] if isinstance(value,tuple) else value for key,value in asdict(self).items()}

    def csv(self,key):return ','.join(getattr(self,key))
