"""Meaning record — bounded snapshot of civilization-local semantic state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from observability.v04.metric_normalizer import clamp01


@dataclass
class MeaningRecord:
    """Single bounded meaning snapshot — never claims immutable ontology."""

    record_id: str
    concept_id: str
    runtime_id: str
    summary: str
    confidence: float = 0.7
    interpretive_hint: float = 0.0
    retention_hours: float = 168.0
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        concept_id: str,
        runtime_id: str,
        summary: str,
        confidence: float = 0.7,
        interpretive_hint: float = 0.0,
        retention_hours: float = 168.0,
        metadata: dict[str, Any] | None = None,
    ) -> MeaningRecord:
        return cls(
            record_id=str(uuid4()),
            concept_id=concept_id,
            runtime_id=runtime_id,
            summary=summary,
            confidence=clamp01(confidence),
            interpretive_hint=clamp01(interpretive_hint),
            retention_hours=max(1.0, retention_hours),
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "concept_id": self.concept_id,
            "runtime_id": self.runtime_id,
            "summary": self.summary,
            "confidence": round(self.confidence, 4),
            "interpretive_hint": round(self.interpretive_hint, 4),
            "retention_hours": round(self.retention_hours, 2),
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
            "advisory_only": True,
        }
