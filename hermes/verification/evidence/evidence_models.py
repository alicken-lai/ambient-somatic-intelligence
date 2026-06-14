"""Evidence data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source_type: str
    source_reference: str
    confidence: float
    supports_claims: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_type": self.source_type,
            "source_reference": self.source_reference,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "supports_claims": self.supports_claims,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Evidence":
        return cls(
            evidence_id=str(raw["evidence_id"]),
            source_type=str(raw["source_type"]),
            source_reference=str(raw["source_reference"]),
            confidence=float(raw.get("confidence", 0.0)),
            timestamp=str(raw.get("timestamp", datetime.now(timezone.utc).isoformat())),
            supports_claims=list(raw.get("supports_claims", [])),
        )
