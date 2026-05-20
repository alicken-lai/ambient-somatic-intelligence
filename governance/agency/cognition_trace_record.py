"""Cognition trace record — bounded advisory trace for agency lineage."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class CognitionTraceRecord:
    trace_id: str
    agency_id: str
    runtime_id: str
    label: str
    parent_trace_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create(
        cls,
        *,
        agency_id: str,
        runtime_id: str,
        label: str,
        parent_trace_id: str | None = None,
    ) -> CognitionTraceRecord:
        return cls(
            trace_id=str(uuid4()),
            agency_id=agency_id,
            runtime_id=runtime_id,
            label=label,
            parent_trace_id=parent_trace_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "agency_id": self.agency_id,
            "runtime_id": self.runtime_id,
            "label": self.label,
            "parent_trace_id": self.parent_trace_id,
            "created_at": self.created_at,
            "advisory_only": True,
        }
