from dataclasses import dataclass, field
from types import MappingProxyType

from .identity import ObjectIdentity
from .evidence import Evidence
from .serialization import digest, thaw


def freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({key: freeze(item) for key, item in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(freeze(item) for item in value)
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise ValueError('VALUE_MUST_BE_JSON')


@dataclass(frozen=True, slots=True)
class KnownValue:
    state: str
    value: object
    evidence_ids: tuple[str, ...]

    def __post_init__(self):
        if self.state not in {'KNOWN', 'ABSENT', 'UNKNOWN', 'NOT_APPLICABLE'}:
            raise ValueError('INVALID_KNOWN_VALUE_STATE')
        if self.state != 'KNOWN' and self.value is not None:
            raise ValueError('NON_KNOWN_VALUE_MUST_BE_NULL')
        if self.state == 'ABSENT' and not self.evidence_ids:
            raise ValueError('ABSENCE_REQUIRES_SCOPE_EVIDENCE')
        object.__setattr__(self, 'evidence_ids', tuple(self.evidence_ids))
        object.__setattr__(self, 'value', freeze(self.value))


@dataclass(frozen=True, slots=True)
class Coverage:
    inventory: str
    ddl: str
    dictionary: str
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SnapshotObject:
    identity: ObjectIdentity
    properties: object
    ddl_path: str | None
    ddl_sha256: str | None
    coverage: Coverage
    evidence_ids: tuple[str, ...]
    raw_ddl: bytes | None = field(default=None, repr=False, compare=False)
    projection: object = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, 'properties', MappingProxyType(dict(self.properties)))

    @property
    def object_key(self):
        return self.identity.key

    def to_dict(self):
        identity = self.identity
        return {'object_key': self.object_key,
                'identity': {'profile_id': identity.profile_id, 'owner': identity.owner.effective_name,
                             'object_type': identity.object_type, 'name': identity.name.effective_name,
                             'quoted': identity.name.quoted, 'parent_key': identity.parent_key},
                'properties': thaw(self.properties), 'ddl_path': self.ddl_path, 'ddl_sha256': self.ddl_sha256,
                'coverage': thaw(self.coverage), 'evidence_ids': list(self.evidence_ids)}


@dataclass(frozen=True, slots=True)
class SchemaSnapshot:
    schema_version: str
    synthetic: bool
    side: str
    profile_id: str
    schemas: tuple[str, ...]
    source_commit: str | None
    target_id: str | None
    objects: tuple[SnapshotObject, ...]
    completeness: Coverage
    capabilities: object
    evidence: tuple[Evidence, ...]
    observed_consistency: str
    source_origin: object = None

    def __post_init__(self):
        object.__setattr__(self, 'capabilities', MappingProxyType(dict(self.capabilities)))
        oracle=(self.source_origin is not None and self.source_origin.get('kind')=='ORACLE')
        if oracle:
            import re
            if (set(self.source_origin)!={'kind','connection_id','snapshot_id'}
                    or not isinstance(self.source_origin['connection_id'],str) or not self.source_origin['connection_id']
                    or not re.fullmatch('[0-9a-f]{64}',self.source_origin.get('snapshot_id',''))
                    or self.side!='SOURCE' or self.source_commit is not None):
                raise ValueError('SOURCE_ORIGIN_INVALID')
            object.__setattr__(self,'source_origin',freeze(dict(self.source_origin)))
        elif self.source_origin is not None:raise ValueError('SOURCE_ORIGIN_INVALID')
        if self.side=='SOURCE' and ((self.source_commit is None and not oracle) or self.target_id is not None):
            raise ValueError('SOURCE_SNAPSHOT_REVISION_REQUIRED')
        if self.side=='TARGET' and (self.target_id is None or self.source_commit is not None):
            raise ValueError('TARGET_SNAPSHOT_ID_REQUIRED')
        if self.side not in {'SOURCE','TARGET'}:
            raise ValueError('SNAPSHOT_SIDE_INVALID')
        keys = [item.object_key for item in self.objects]
        if len(keys) != len(set(keys)):
            raise ValueError('DUPLICATE_SNAPSHOT_IDENTITY')

    @property
    def semantic_digest(self):
        # Evidence spans/raw byte formatting and capture time are not semantics.
        state = {'profile_id': self.profile_id, 'schemas': self.schemas, 'coverage': thaw(self.completeness),
                 'capabilities': {k: {'state': v.state, 'value': thaw(v.value)} for k, v in self.capabilities.items()},
                 'objects': [{'key': obj.object_key, 'coverage': thaw(obj.coverage),
                              'properties': {k: {'state': v.state, 'value': thaw(v.value)}
                                             for k, v in obj.properties.items()}}
                             for obj in sorted(self.objects, key=lambda item: item.object_key)]}
        return digest(state)

    def to_dict(self):
        document={'schema_version': self.schema_version, 'synthetic': self.synthetic, 'side': self.side,
                'profile_id': self.profile_id, 'schemas': list(self.schemas), 'source_commit': self.source_commit,
                'target_id': self.target_id, 'objects': [obj.to_dict() for obj in self.objects],
                'coverage': thaw(self.completeness), 'capabilities': thaw(self.capabilities),
                'evidence': thaw(self.evidence), 'observed_consistency': self.observed_consistency,
                'semantic_digest': self.semantic_digest}
        if self.source_origin is not None:document['source_origin']=thaw(self.source_origin)
        return document
