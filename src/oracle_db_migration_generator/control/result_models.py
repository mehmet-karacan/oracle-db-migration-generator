"""Closed, SQL-body-free metadata used by the object results UI."""
import json
from typing import Literal

from pydantic import BaseModel,ConfigDict,Field,JsonValue,field_validator,model_validator


class Closed(BaseModel):
    model_config=ConfigDict(extra='forbid')


class ResultValue(Closed):
    state:Literal['KNOWN','ABSENT','UNKNOWN','NOT_APPLICABLE']
    value:JsonValue=None
    omitted:bool=False

    @model_validator(mode='after')
    def bounded(self):
        if self.omitted or self.state!='KNOWN':self.value=None
        if len(json.dumps(self.value,ensure_ascii=False))>32768:raise ValueError('RESULT_VALUE_TOO_LARGE')
        return self


def metadata_path(path):
    parts=path.strip('/').split('/')
    return (parts[0] in {'columns','constraints','index','sequence','table_properties','trigger','editionable','presence','coverage'}
            and not any(part in {'definition','structured','ddl','sql','body','statement'} for part in parts))


class ResultDifference(Closed):
    id:str=Field(min_length=1,max_length=512)
    object_key:str=Field(pattern=r'^[a-f0-9]{64}$')
    property_path:str=Field(min_length=1,max_length=2048)
    kind:Literal['MISSING','EXTRA','CHANGED','UNKNOWN','INFORMATIONAL']
    source:ResultValue
    target:ResultValue
    evidence_ids:list[str]=Field(default_factory=list,max_length=10000)

    @model_validator(mode='after')
    def no_bodies(self):
        if not metadata_path(self.property_path):
            self.source.value=self.target.value=None
            self.source.omitted=self.target.omitted=True
        return self


class ResultIdentity(Closed):
    profile_id:str=Field(min_length=1,max_length=128)
    owner:str=Field(min_length=1,max_length=512)
    object_type:str=Field(min_length=1,max_length=64)
    name:str=Field(min_length=1,max_length=512)
    quoted:bool
    parent_key:str|None=None
    display_name:str|None=Field(default=None,max_length=1024)


class ResultOperation(Closed):
    id:str=Field(min_length=1,max_length=512)
    object:ResultIdentity
    kind:str=Field(min_length=1,max_length=128)
    decision:Literal['READY','REVIEW_REQUIRED','BLOCKED','INFORMATIONAL']
    reason_tr:str=Field(max_length=65536)
    change_ids:list[str]=Field(max_length=100000)
    evidence_ids:list[str]=Field(default_factory=list,max_length=10000)
    depends_on:list[str]=Field(default_factory=list,max_length=10000)
    sql_path:str|None=None

    @field_validator('sql_path')
    @classmethod
    def safe_sql_path(cls,path):
        if path is not None and (not path or path.startswith('/') or '\\' in path or ':' in path
                or any(s in {'','..','.'} for s in path.split('/')) or not path.endswith('.sql')):
            raise ValueError('RESULT_SQL_PATH_UNSAFE')
        return path


class ResultScope(Closed):
    inventory:Literal['COMPLETE','PARTIAL','UNKNOWN']
    ddl:Literal['COMPLETE','PARTIAL','UNKNOWN']
    dictionary:Literal['COMPLETE','PARTIAL','UNKNOWN']
    diagnostics:list[str]=Field(max_length=10000)


class ResultCounts(Closed):
    observed_differences:int=Field(ge=0)
    ready_operations:int=Field(ge=0)
    review_operations:int=Field(ge=0)
    blocked_operations:int=Field(ge=0)
    informational_changes:int=Field(ge=0)


class ResultView(Closed):
    schema_version:Literal['comparison-view/1.0']
    plan_id:str=Field(pattern=r'^[a-f0-9]{64}$')
    source_commit:str|None=Field(pattern=r'^([a-f0-9]{40}|[a-f0-9]{64})$')
    target_id:str=Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$')
    synthetic:bool
    scope:ResultScope
    counts:ResultCounts
    differences:list[ResultDifference]=Field(max_length=200000)
    operations:list[ResultOperation]=Field(max_length=100000)

    @model_validator(mode='after')
    def consistent(self):
        ids=[r.id for r in self.differences];op_ids=[o.id for o in self.operations]
        if len(set(ids))!=len(ids) or len(set(op_ids))!=len(op_ids):raise ValueError('RESULT_DUPLICATE_IDS')
        known=set(ids)
        if any(set(o.change_ids)-known for o in self.operations):raise ValueError('RESULT_CHANGE_LINK_MISSING')
        if self.counts.observed_differences!=len(ids):raise ValueError('RESULT_COUNTS_MISMATCH')
        mapping={'ready_operations':'READY','review_operations':'REVIEW_REQUIRED','blocked_operations':'BLOCKED','informational_changes':'INFORMATIONAL'}
        if any(getattr(self.counts,k)!=sum(o.decision==v for o in self.operations) for k,v in mapping.items()):
            raise ValueError('RESULT_COUNTS_MISMATCH')
        return self
