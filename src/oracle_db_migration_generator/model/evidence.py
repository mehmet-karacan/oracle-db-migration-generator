from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Evidence:
    id: str
    kind: str
    side: str
    path: str | None
    sha256: str | None
    start_line: int | None
    end_line: int | None
    query_id: str | None
    detail_tr: str
    start_byte: int | None = None
    end_byte: int | None = None


@dataclass(frozen=True, slots=True)
class EvidenceRegistry:
    records: tuple[Evidence, ...]

    def get(self, evidence_id: str) -> Evidence:
        return next(item for item in self.records if item.id == evidence_id)
