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
    evidence: tuple = field(init=False,repr=False)
    policy_evidence: object = field(init=False,repr=False)

    def __post_init__(self):
        object.__setattr__(self,'source_objects',MappingProxyType({obj.object_key:obj for obj in self.source.objects}))
        object.__setattr__(self,'target_objects',MappingProxyType({obj.object_key:obj for obj in self.target.objects}))
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
        values = self.source_objects.values() if desired else self.target_objects.values()
        return next((obj for obj in values if obj.identity.owner.effective_name==owner
                     and obj.identity.object_type==kind and obj.identity.name.effective_name==name),None)

    def new_table(self,owner,name):
        return self.lookup(owner,'TABLE',name) is not None and self.lookup(owner,'TABLE',name,desired=False) is None
