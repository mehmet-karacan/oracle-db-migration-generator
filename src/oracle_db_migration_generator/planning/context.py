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
    _sequence_consumers: object = field(default=None,init=False,repr=False,compare=False)
    evidence: tuple = field(init=False,repr=False)
    policy_evidence: object = field(init=False,repr=False)

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

    def existing_sequence_consumers(self,owner,name):
        """Index all existing raw source consumers once for this plan context."""
        if self._sequence_consumers is None:
            from ..parsing.dependencies import references
            consumers={}
            # Report filtering must not hide a consumer's existing-data risk.
            for obj in self.source.objects:
                if obj.object_key not in self.target_objects:
                    continue
                sequences={(ref.owner,ref.name) for ref in references(obj) if ref.object_type=='SEQUENCE'}
                for sequence in sequences:
                    consumers.setdefault(sequence,[]).append(obj)
            object.__setattr__(self,'_sequence_consumers',MappingProxyType({key:tuple(values) for key,values in consumers.items()}))
        return self._sequence_consumers.get((owner,name),())

    def new_table(self,owner,name):
        return self.lookup(owner,'TABLE',name) is not None and self.lookup(owner,'TABLE',name,desired=False) is None
