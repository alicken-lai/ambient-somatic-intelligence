"""Truth edges — typed dependency relationships between truth nodes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EdgeKind(str, Enum):
    """Relationship between truth nodes."""

    DEPENDS_ON = "depends_on"
    DERIVES_FROM = "derives_from"
    INVALIDATES = "invalidates"
    REFERENCES = "references"


@dataclass(frozen=True)
class TruthEdge:
    """Directed edge in the truth graph."""

    source_id: str
    target_id: str
    kind: EdgeKind = EdgeKind.DEPENDS_ON
    owner: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.source_id or not self.target_id:
            raise ValueError("TruthEdge requires non-empty source_id and target_id")
        if self.source_id == self.target_id:
            raise ValueError("TruthEdge cannot be self-referential")
        if not isinstance(self.kind, EdgeKind):
            object.__setattr__(self, "kind", EdgeKind(str(self.kind)))

    def to_dict(self) -> dict[str, str]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "kind": self.kind.value,
            "owner": self.owner,
            "timestamp": self.timestamp,
        }
