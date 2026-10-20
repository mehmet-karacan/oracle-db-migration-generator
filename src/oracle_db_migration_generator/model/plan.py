from dataclasses import dataclass, field, replace

from .identity import ObjectIdentity
from .serialization import digest, thaw
from .snapshot import KnownValue


@dataclass(frozen=True, slots=True)
class DependencyReference:
    owner: str
    object_type: str
    name: str
    role: str
    columns: tuple[str, ...] = ()
    unqualified: bool = False


@dataclass(frozen=True, slots=True)
class SqlIntent:
    statement: bytes = field(repr=False)
    statement_kind: str
    phase: int
    references: tuple[DependencyReference, ...] = ()
    feature_scope: str = 'OBJECT'
    verification_sha256: str | None = None
    affected_columns: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Condition:
    id: str
    kind: str
    status: str
    reason_code: str
    evidence_ids: tuple[str, ...]
    check_path: str | None = None


@dataclass(frozen=True, slots=True)
class Operation:
    operation_id: str
    identity: ObjectIdentity
    kind: str
    before: KnownValue
    after: KnownValue
    decision: str
    risk: str
    rule_id: str
    reason_codes: tuple[str, ...]
    reason_tr: str
    change_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    dependencies: tuple[str, ...] = ()
    sql: object = None
    preconditions: tuple[Condition, ...] = ()
    postconditions: tuple[Condition, ...] = ()
    intent: SqlIntent | None = field(default=None,repr=False,compare=False)

    def to_dict(self):
        identity = self.identity
        return {'id':self.operation_id,'object':{'profile_id':identity.profile_id,'owner':identity.owner.effective_name,
                'object_type':identity.object_type,'name':identity.name.effective_name,'quoted':identity.name.quoted,
                'parent_key':identity.parent_key},'kind':self.kind,'before':thaw(self.before),'after':thaw(self.after),
                'decision':self.decision,'risk':self.risk,'rule_id':self.rule_id,'reason_codes':list(self.reason_codes),
                'reason_tr':self.reason_tr,'change_ids':list(self.change_ids),'evidence_ids':list(self.evidence_ids),
                'depends_on':list(self.dependencies),'sql':thaw(self.sql),'preconditions':thaw(self.preconditions),
                'postconditions':thaw(self.postconditions)}


@dataclass(frozen=True, slots=True)
class TargetPlan:
    synthetic: bool
    generator_version: str
    rule_version: str
    source: object
    target: object
    target_snapshot_digest: str
    scope: object
    status: str
    operations: tuple[Operation, ...]
    differences: tuple
    evidence: tuple
    input_fingerprint: object
    warnings: tuple[str, ...] = ()
    validation: object = None
    schema_version: str = 'plan/1.0'

    @property
    def counts(self):
        return {'observed_differences':len(self.differences),
                'ready_operations':sum(op.decision=='READY' for op in self.operations),
                'review_operations':sum(op.decision=='REVIEW_REQUIRED' for op in self.operations),
                'blocked_operations':sum(op.decision=='BLOCKED' for op in self.operations),
                'informational_changes':sum(op.decision=='INFORMATIONAL' for op in self.operations)}

    def _document(self):
        return {'schema_version':self.schema_version,'synthetic':self.synthetic,'generator_version':self.generator_version,
                'rule_version':self.rule_version,'source':thaw(self.source),'target':thaw(self.target),
                'target_snapshot_digest':self.target_snapshot_digest,'scope':thaw(self.scope),'status':self.status,
                'counts':self.counts,'operations':[op.to_dict() for op in self.operations],
                'differences':[diff.to_dict() for diff in self.differences],'evidence':thaw(self.evidence),
                'input_fingerprint':thaw(self.input_fingerprint),'warnings':list(self.warnings)}

    @property
    def plan_id(self):
        core = self._document()
        for operation in core['operations']:
            operation['sql'] = None
        return digest(core)

    def to_dict(self):
        result = self._document()
        result['plan_id'] = self.plan_id
        result['validation'] = thaw(self.validation) if self.validation is not None else {
            'level':'NOT_VALIDATED','execution_status':'NOT_EXECUTED','checks':[],
            'limitations_tr':['SQL üretilmesi veritabanında uygulama veya canlı syntax/compile doğrulaması değildir.']}
        return result

    def with_operations(self,operations,**changes):
        return replace(self,operations=tuple(operations),**changes)
