"""Motivational trace record — append-only advisory trace for purpose evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class MotivationalTraceRecord:
    trace_id: str
    purpose_id: str
    runtime_id: str
    event: str
    payload_hash: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create(
        cls,
        *,
        purpose_id: str,
        runtime_id: str,
        event: str,
        payload_hash: str = "",
    ) -> MotivationalTraceRecord:
        return cls(
            trace_id=str(uuid4()),
            purpose_id=purpose_id,
            runtime_id=runtime_id,
            event=event,
            payload_hash=payload_hash,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "purpose_id": self.purpose_id,
            "runtime_id": self.runtime_id,
            "event": self.event,
            "payload_hash": self.payload_hash,
            "created_at": self.created_at,
            "advisory_only": True,
        }
