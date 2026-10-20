from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SchemaRoot:
    path: str
    source_schema: str


@dataclass(frozen=True, slots=True)
class Policy:
    allow_drop: bool
    allow_schema_remap: bool
    compare_physical_storage: bool
    grant_allowlist: tuple[str, ...]
    existing_sequence_state: str
    require_complete_metadata: bool
    exclude_system_generated: bool = False
    excluded_object_types: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SourceProfile:
    schema_version: str
    id: str
    layout: str
    layout_version: int
    schema_roots: tuple[SchemaRoot, ...]
    object_types: tuple[str, ...]
    source_length_semantics: str
    policy: Policy


@dataclass(frozen=True, slots=True)
class Endpoint:
    host: str = field(repr=False)
    port: int
    service_name: str | None = field(default=None, repr=False)
    sid: str | None = field(default=None, repr=False)


@dataclass(frozen=True, slots=True)
class SchemaMapping:
    source_schema: str
    target_schema: str
    credential_id: str = field(repr=False)
    metadata_reader: str | None = None


@dataclass(frozen=True, slots=True)
class TargetConfig:
    id: str
    name: str
    enabled: bool
    endpoint: Endpoint
    driver_mode: str
    schema_mappings: tuple[SchemaMapping, ...]
    capture_timeout_seconds: int = 900
