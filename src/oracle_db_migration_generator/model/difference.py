from dataclasses import dataclass

from .serialization import thaw
from .snapshot import Coverage, KnownValue


@dataclass(frozen=True, slots=True)
class Difference:
    difference_id: str
    object_key: str
    property_path: str
    before: KnownValue
    after: KnownValue
    kind: str
    evidence_ids: tuple[str, ...]

    def to_dict(self):
        return {'id':self.difference_id,'object_key':self.object_key,'property_path':self.property_path,
                'before':thaw(self.before),'after':thaw(self.after),'kind':self.kind,'evidence_ids':list(self.evidence_ids)}


@dataclass(frozen=True, slots=True)
class DifferenceSet:
    source_fingerprint: str
    target_fingerprint: str
    differences: tuple[Difference, ...]
    scope: Coverage
    diagnostics: tuple[str, ...]

    @property
    def complete(self):
        return not self.diagnostics and not any(diff.kind=='UNKNOWN' for diff in self.differences)
