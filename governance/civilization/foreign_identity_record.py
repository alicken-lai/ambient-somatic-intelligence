"""Foreign identity record — tracked separately, never merged with local identity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class ForeignIdentityRecord:
    record_id: str
    sovereign_id: str
    domain: str
    trust_tier: str = "observational"
    merge_forbidden: bool = True
    observed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_sovereign(cls, sovereign_id: str, *, domain: str = "external") -> ForeignIdentityRecord:
        return cls(
            record_id=f"foreign-{uuid4().hex[:12]}",
            sovereign_id=sovereign_id,
            domain=domain,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "sovereign_id": self.sovereign_id,
            "domain": self.domain,
            "trust_tier": self.trust_tier,
            "merge_forbidden": self.merge_forbidden,
            "observed_at": self.observed_at,
            "metadata": dict(self.metadata),
        }
