"""Trust record models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class TrustRecord:
    trust_id: str
    entity_type: str
    entity_id: str
    trust_score: float
    reasoning: list[str] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "trust_id": self.trust_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "trust_score": self.trust_score,
            "reasoning": self.reasoning,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "TrustRecord":
        return cls(
            trust_id=str(raw["trust_id"]),
            entity_type=str(raw["entity_type"]),
            entity_id=str(raw["entity_id"]),
            trust_score=float(raw.get("trust_score", 0.0)),
            reasoning=list(raw.get("reasoning", [])),
            last_updated=str(raw.get("last_updated", datetime.now(timezone.utc).isoformat())),
        )
