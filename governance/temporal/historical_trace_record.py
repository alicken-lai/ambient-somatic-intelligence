"""Historical trace record — append-only labeled trace, no autonomous rewrite."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class HistoricalTraceRecord:
    trace_id: str
    epoch_id: str
    runtime_id: str
    claim: str
    advisory_only: bool = True
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @classmethod
    def create(
        cls,
        *,
        epoch_id: str,
        runtime_id: str,
        claim: str,
    ) -> HistoricalTraceRecord:
        return cls(
            trace_id=str(uuid4()),
            epoch_id=epoch_id,
            runtime_id=runtime_id,
            claim=claim,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "epoch_id": self.epoch_id,
            "runtime_id": self.runtime_id,
            "claim": self.claim,
            "advisory_only": self.advisory_only,
            "created_at": self.created_at,
        }
