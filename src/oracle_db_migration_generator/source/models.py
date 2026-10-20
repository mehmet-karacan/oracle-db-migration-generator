from dataclasses import dataclass, field
from typing import Protocol

from ..config.loader import ConfigError


class SourceError(ConfigError):
    exit_code = 30


@dataclass(frozen=True, slots=True)
class GitEntry:
    path: str
    mode: str
    kind: str
    object_id: str
    raw: bytes | None = field(default=None, repr=False)


class RepositoryReader(Protocol):
    def resolve_commit(self, ref: str) -> str: ...
    def entries(self, commit: str) -> tuple[GitEntry, ...]: ...
    def read_blobs(self, object_ids: tuple[str, ...]) -> dict[str, bytes]: ...


@dataclass(frozen=True, slots=True)
class SourceRevision:
    commit: str
    repository: RepositoryReader = field(repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class SourceArtifact:
    path: str
    source_schema: str
    kind: str
    object_type_hint: str | None
    raw: bytes = field(repr=False)
    sha256: str


@dataclass(frozen=True, slots=True)
class SourceInput:
    revision: SourceRevision
    artifacts: tuple[SourceArtifact, ...]
    input_digest: str
    profile: object = field(default=None, repr=False)
