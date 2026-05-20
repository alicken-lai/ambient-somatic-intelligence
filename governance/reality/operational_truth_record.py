"""Operational truth record — local sovereign operational claim."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class OperationalTruthRecord:
    """A bounded operational truth claim — never authoritative over Guardian."""

    record_id: str
    runtime_id: str
    claim: str
    confidence: float = 0.5
    uncertainty: float = 0.35
    provenance: dict[str, Any] = field(default_factory=dict)
    advisory_only: bool = True
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "runtime_id": self.runtime_id,
            "claim": self.claim,
            "confidence": round(self.confidence, 4),
            "uncertainty": round(self.uncertainty, 4),
            "provenance": dict(self.provenance),
            "advisory_only": self.advisory_only,
            "created_at": self.created_at,
        }
