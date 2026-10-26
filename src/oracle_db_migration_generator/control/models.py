"""Closed control-plane inputs. Credentials never enter public documents."""
import re
from typing import Annotated,Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

OBJECT_TYPES=('TABLE','INDEX','SEQUENCE','VIEW','PACKAGE_SPEC','PACKAGE_BODY','PROCEDURE',
              'FUNCTION','TRIGGER','TYPE_SPEC','TYPE_BODY','SYNONYM','COMMENT','GRANT',
              'MATERIALIZED_VIEW','MATERIALIZED_VIEW_LOG')


class ClosedModel(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)


class ConnectionInput(ClosedModel):
    project_id:str|None=Field(default=None,pattern=r'^[a-f0-9]{32}$')
    name:str=Field(min_length=1,max_length=100)
    kind:Literal['GIT','ORACLE','SNAPSHOT']
    capture_id:str|None=Field(default=None,pattern=r'^[a-f0-9]{32}$')
    host:str|None=None
    port:int=Field(default=1521,ge=1,le=65535)
    service_name:str|None=None
    sid:str|None=None
    repository:str|None=None
    username:str|None=Field(default=None,max_length=256)
    password:Annotated[str,StringConstraints(strip_whitespace=False)]|None=Field(default=None,max_length=4096)
    driver_mode:Literal['thin','thick']='thin'
    metadata_reader:str|None=None
    allowed_users:list[str]=Field(default_factory=list,max_length=100)

    @model_validator(mode='after')
    def validate_endpoint(self):
        if any(not re.fullmatch(r'[A-Za-z0-9_.@-]{1,128}',u) for u in self.allowed_users):
            raise ValueError('USER_ID_INVALID')
        if self.kind=='SNAPSHOT':
            if not self.capture_id or any((self.username,self.password,self.host,self.repository,self.metadata_reader,self.service_name,self.sid)):
                raise ValueError('CAPTURE_CONNECTION_INVALID')
            return self
        if self.capture_id:raise ValueError('CAPTURE_CONNECTION_INVALID')
        if self.kind=='ORACLE':
            if not self.host or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,253}',self.host):
                raise ValueError('ORACLE_HOST_INVALID')
            if bool(self.service_name)==bool(self.sid):raise ValueError('ORACLE_SERVICE_OR_SID_REQUIRED')
            if any(v and (len(v)>128 or re.search(r'[\s/@\\]',v)) for v in (self.service_name,self.sid)):
                raise ValueError('ORACLE_SERVICE_INVALID')
        else:
            p=urlsplit(self.repository or '')
            if (p.scheme!='https' or not p.hostname or p.username or p.password or p.query or p.fragment
                    or any(c.isspace() for c in self.repository or '')):raise ValueError('GIT_URL_INVALID')
        return self


class SourceSelection(ClosedModel):
    kind:Literal['GIT','ORACLE','SNAPSHOT']
    connection_id:str=Field(pattern=r'^[a-f0-9]{32}$')
    schemas:list[str]=Field(min_length=1,max_length=20)
    ref:str='master'
    layout:Literal['by_object','flat']='by_object'
    roots:dict[str,str]=Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_scope(self):
        if len(set(self.schemas))!=len(self.schemas) or any(not re.fullmatch(r'[A-Za-z][A-Za-z0-9_$#]{0,127}',s) for s in self.schemas):
            raise ValueError('SCHEMA_SCOPE_INVALID')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,100}',self.ref) or '..' in self.ref:
            raise ValueError('GIT_REF_INVALID')
        if set(self.roots)-set(self.schemas):raise ValueError('ROOT_OUTSIDE_SCHEMA_SCOPE')
        for root in self.roots.values():
            if not root or root.startswith('/') or '\\' in root or ':' in root or any(s in {'.','..'} for s in root.split('/')):
                raise ValueError('SOURCE_ROOT_UNSAFE')
        return self


class SchemaPair(ClosedModel):
    source_schema:str=Field(pattern=r'^[A-Za-z][A-Za-z0-9_$#]{0,127}$')
    target_schema:str=Field(pattern=r'^[A-Za-z][A-Za-z0-9_$#]{0,127}$')


def validate_schema_pairs(schemas,target_ids,mappings):
    if set(mappings)!=set(target_ids):raise ValueError('TARGET_SCHEMA_SCOPE_REQUIRED')
    for pairs in mappings.values():
        if not 1<=len(pairs)<=20:raise ValueError('TARGET_SCHEMA_SCOPE_REQUIRED')
        if len({m.source_schema for m in pairs})!=len(pairs):raise ValueError('DUPLICATE_SCHEMA_MAPPING')
        for pair in pairs:
            if pair.source_schema not in schemas:raise ValueError('TARGET_SCHEMA_OUTSIDE_SOURCE_SCOPE')
            if pair.source_schema!=pair.target_schema:raise ValueError('SCHEMA_REMAP_NOT_SUPPORTED')


def schema_scope(data):
    source=data['source']
    return {'source':{k:source[k] for k in ('kind','connection_id')},'schemas':sorted(source['schemas']),
            'targets':sorted(data['target_ids']),
            'mappings':{key:sorted(value,key=lambda m:(m['source_schema'],m['target_schema']))
                        for key,value in data['target_mappings'].items()}}


class SchemaMappingInput(ClosedModel):
    project_id:str|None=Field(default=None,pattern=r'^[a-f0-9]{32}$')
    name:str=Field(min_length=1,max_length=100)
    source:SourceSelection
    target_ids:list[str]=Field(min_length=1,max_length=8)
    target_mappings:dict[str,list[SchemaPair]]

    @model_validator(mode='after')
    def validate_scope(self):
        if len(set(self.target_ids))!=len(self.target_ids) or any(not re.fullmatch(r'[a-f0-9]{32}',id) for id in self.target_ids):
            raise ValueError('PROFILE_SCOPE_INVALID')
        validate_schema_pairs(self.source.schemas,self.target_ids,self.target_mappings)
        return self


class ProfileInput(ClosedModel):
    project_id:str|None=Field(default=None,pattern=r'^[a-f0-9]{32}$')
    name:str=Field(min_length=1,max_length=100)
    source:SourceSelection
    target_ids:list[str]=Field(min_length=1,max_length=8)
    target_mappings:dict[str,list[SchemaPair]]|None=None
    mapping_id:str|None=Field(default=None,pattern=r'^[a-f0-9]{32}$')
    mapping_revision:int|None=Field(default=None,ge=1)
    object_types:list[str]=Field(default_factory=lambda:list(OBJECT_TYPES))
    excluded_object_types:list[str]=Field(default_factory=lambda:['GRANT'])
    exclude_system_generated:bool=True
    compare_physical_storage:bool=False
    source_length_semantics:Literal['BYTE','CHAR','UNKNOWN']='UNKNOWN'
    capture_filter:dict|None=None

    @model_validator(mode='after')
    def validate_types(self):
        if self.capture_filter is not None:
            from ..portable.selection import CaptureFilter
            self.capture_filter=CaptureFilter.from_dict({**self.capture_filter,'schemas':self.source.schemas}).to_dict()
        if (not self.object_types or set(self.object_types)-set(OBJECT_TYPES)
                or set(self.excluded_object_types)-set(OBJECT_TYPES)
                or len(set(self.target_ids))!=len(self.target_ids)
                or any(not re.fullmatch(r'[a-f0-9]{32}',x) for x in self.target_ids)):
            raise ValueError('PROFILE_SCOPE_INVALID')
        if self.target_mappings is not None:
            validate_schema_pairs(self.source.schemas,self.target_ids,self.target_mappings)
        if (self.mapping_id is None)!=(self.mapping_revision is None):raise ValueError('SCHEMA_MAPPING_REFERENCE_INVALID')
        if self.mapping_id is not None and self.target_mappings is None:raise ValueError('TARGET_SCHEMA_SCOPE_REQUIRED')
        return self


class SettingsInput(ClosedModel):
    capture_timeout_seconds:int=Field(default=900,ge=30,le=7200)
    connect_timeout_seconds:int=Field(default=8,ge=1,le=60)
    call_timeout_ms:int=Field(default=15000,ge=1000,le=120000)
    parser_regular_seconds:int=Field(default=30,ge=1,le=600)
    parser_large_seconds:int=Field(default=120,ge=1,le=600)
    parser_package_seconds:int=Field(default=240,ge=1,le=600)
    job_timeout_seconds:int=Field(default=7200,ge=60,le=14400)
    git_attempts:int=Field(default=3,ge=1,le=5)
    git_retry_seconds:int=Field(default=10,ge=0,le=60)
    max_parallel_jobs:int=Field(default=1,ge=1,le=4)
    cache_enabled:bool=True
    cache_entries:int=Field(default=4,ge=1,le=16)
    cache_megabytes:int=Field(default=1024,ge=64,le=4096)
    notify_enabled:bool=True
    # Existing authorization: this control plane cannot add mail recipients.
    notify_to:Literal['mkaracan@innova.com.tr']='mkaracan@innova.com.tr'


class ProjectInput(ClosedModel):
    name:str=Field(min_length=1,max_length=100)
    code:str=Field(pattern=r'^[A-Z][A-Z0-9_-]{0,29}$')
