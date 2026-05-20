"""Constitutional intent trace — append-only motivational trace metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class ConstitutionalIntentTrace:
    trace_id: str
    intent_id: str
    constitutional_ref: str
    summary: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create(cls, *, intent_id: str, constitutional_ref: str, summary: str) -> ConstitutionalIntentTrace:
        return cls(
            trace_id=str(uuid4()),
            intent_id=intent_id,
            constitutional_ref=constitutional_ref,
            summary=summary,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "intent_id": self.intent_id,
            "constitutional_ref": self.constitutional_ref,
            "summary": self.summary,
            "created_at": self.created_at,
            "advisory_only": True,
        }
