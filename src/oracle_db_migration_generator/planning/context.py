"""Oracle DB Migration Generator planının kaynak ve hedef nesnelerini tutar.

Author: Mehmet KARACAN
Date: 2026-11-02
"""

from dataclasses import dataclass, field
from types import MappingProxyType

from ..model.evidence import Evidence
from ..model.serialization import digest


@dataclass(frozen=True)
class PlanningContext:
    source: object
    target: object
    profile: object
    target_name: str
    parser_hash_override: str | None = None
    source_objects: object = field(init=False,repr=False)
    target_objects: object = field(init=False,repr=False)
    _source_lookup: object = field(init=False,repr=False,compare=False)
    _target_lookup: object = field(init=False,repr=False,compare=False)
    evidence: tuple = field(init=False,repr=False)
    policy_evidence: object = field(init=False,repr=False)
    _column_fields: dict = field(default_factory=dict,init=False,repr=False,compare=False)
    _canonical_fields: dict = field(default_factory=dict,init=False,repr=False,compare=False)

    def __post_init__(self):
        object.__setattr__(self,'source_objects',MappingProxyType({obj.object_key:obj for obj in self.source.objects}))
        object.__setattr__(self,'target_objects',MappingProxyType({obj.object_key:obj for obj in self.target.objects}))
        for objects,attribute in ((self.source_objects,'_source_lookup'),(self.target_objects,'_target_lookup')):
            lookup={}
            for obj in objects.values():
                identity=obj.identity
                lookup.setdefault((identity.owner.effective_name,identity.object_type,identity.name.effective_name),obj)
            object.__setattr__(self,attribute,MappingProxyType(lookup))
        policy = Evidence('ev-'+digest(['policy',self.profile.policy]),'POLICY','POLICY',None,digest(self.profile.policy),
                          None,None,None,'Bu planın güvenlik politikası ve grant allowlist kaydı.')
        records = {}
        for item in (*self.source.evidence,*self.target.evidence,policy):
            if item.id in records and records[item.id]!=item:
                raise ValueError('EVIDENCE_ID_CONFLICT')
            records[item.id] = item
        object.__setattr__(self,'evidence',tuple(records[key] for key in sorted(records)))
        object.__setattr__(self,'policy_evidence',policy)

    def lookup(self,owner,kind,name,*,desired=True):
        lookup = self._source_lookup if desired else self._target_lookup
        return lookup.get((owner,kind,name))

    def new_table(self,owner,name):
        return self.lookup(owner,'TABLE',name) is not None and self.lookup(owner,'TABLE',name,desired=False) is None

    def column_fields(self,obj,*,desired=True):
        """Aynı nesnenin kolon kanıtlarını yalnız bu plan içinde yeniden kullanır."""
        key=(desired,id(obj))
        if key not in self._column_fields:
            from .table_rules import column_fields
            snapshot=self.source if desired else self.target
            values=column_fields(obj,snapshot,self.profile.policy)
            result=MappingProxyType({name:MappingProxyType(dict(fields)) for name,fields in values.items()})
            self._column_fields[key]=(obj,result)
        return self._column_fields[key][1]

    def canonical_fields(self,obj,*,desired=True):
        """Nesne alanlarını kaynak veya hedef snapshot kanıtıyla ayrı saklar."""
        key=(desired,id(obj))
        if key not in self._canonical_fields:
            from ..compare.projection_adapter import canonical_fields
            snapshot=self.source if desired else self.target
            self._canonical_fields[key]=(obj,MappingProxyType(canonical_fields(obj,snapshot,self.profile.policy)))
        return self._canonical_fields[key][1]
