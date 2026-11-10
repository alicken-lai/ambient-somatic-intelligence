"""Evidence source models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class EvidenceSource:
    source_id: str
    source_type: str
    trust_level: float
    enabled: bool = True
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "trust_level": self.trust_level,
            "enabled": self.enabled,
            "last_updated": self.last_updated,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "EvidenceSource":
        return cls(
            source_id=str(raw["source_id"]),
            source_type=str(raw["source_type"]),
            trust_level=float(raw.get("trust_level", 0.5)),
            enabled=bool(raw.get("enabled", True)),
            last_updated=str(raw.get("last_updated", datetime.now(timezone.utc).isoformat())),
            metadata=dict(raw.get("metadata", {})),
        )
