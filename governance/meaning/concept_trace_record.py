"""Concept trace record — bounded lineage snapshot for semantic provenance."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class ConceptTraceRecord:
    trace_id: str
    concept_id: str
    parent_concept_id: str | None
    runtime_id: str
    label: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @classmethod
    def create(
        cls,
        *,
        concept_id: str,
        runtime_id: str,
        label: str,
        parent_concept_id: str | None = None,
    ) -> ConceptTraceRecord:
        return cls(
            trace_id=str(uuid4()),
            concept_id=concept_id,
            parent_concept_id=parent_concept_id,
            runtime_id=runtime_id,
            label=label,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "concept_id": self.concept_id,
            "parent_concept_id": self.parent_concept_id,
            "runtime_id": self.runtime_id,
            "label": self.label,
            "created_at": self.created_at,
            "advisory_only": True,
        }
