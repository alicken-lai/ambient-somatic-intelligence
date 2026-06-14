"""Backend-neutral candidate recall interface.

This module defines contracts only. It does not implement a vector backend,
does not select a production default, and does not modify existing memory,
Guardian, Replay, runtime, or kernel behavior.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


SAFETY_DEFAULTS = {
    "guardian_visible": True,
    "decision_allowed": False,
    "action_allowed": False,
    "no_decision_made": True,
}


@dataclass(frozen=True)
class RecallFilter:
    """Backend-neutral filters applied before or during candidate recall."""

    privacy_class: list[str] = field(default_factory=list)
    governance_state: list[str] = field(default_factory=list)
    source_node: list[str] = field(default_factory=list)
    event_type: list[str] = field(default_factory=list)
    modality: list[str] = field(default_factory=list)
    retention_policy: list[str] = field(default_factory=list)
    time_range: dict[str, str] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def applied(self) -> list[str]:
        """Return human-readable non-empty filters."""
        rows: list[str] = []
        for name, value in (
            ("privacy_class", self.privacy_class),
            ("governance_state", self.governance_state),
            ("source_node", self.source_node),
            ("event_type", self.event_type),
            ("modality", self.modality),
            ("retention_policy", self.retention_policy),
            ("time_range", self.time_range),
            ("tags", self.tags),
        ):
            if value:
                rows.append(f"{name}={value}")
        return rows


@dataclass(frozen=True)
class RecallQueryContext:
    """Context needed to export a recall evidence packet."""

    recall_id: str
    timestamp: str
    query_type: str
    query_summary: str
    query_hash: str
    initiating_agent: str
    source_node: str
    vector_backend: str = "none"
    embedding_model: str = "none"
    ranking_method: str = "backend_candidate_ranking"
    replay_reference: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RecallProvenance:
    """Source provenance for a candidate recall result."""

    source_path: str = ""
    source_line: int | None = None
    content_hash: str = ""
    backend: str = ""

    def to_evidence(self, record_id: str, rank: int) -> dict[str, Any]:
        return {
            "record_id": record_id,
            "source_path": self.source_path,
            "source_line": self.source_line,
            "content_hash": self.content_hash,
            "backend": self.backend,
            "rank": rank,
        }


@dataclass(frozen=True)
class RecallResult:
    """Backend-neutral candidate recall result."""

    record_id: str
    score: float
    rank: int
    backend: str
    embedding_model: str
    provenance: RecallProvenance
    filters_applied: list[str] = field(default_factory=list)
    privacy_filters_applied: list[str] = field(default_factory=list)
    governance_filters_applied: list[str] = field(default_factory=list)
    excluded_reason: str = ""
    replay_pointer: dict[str, Any] = field(default_factory=dict)
    decision_allowed: bool = False
    action_allowed: bool = False

    def __post_init__(self) -> None:
        if self.decision_allowed is not False:
            raise ValueError("recall results must not allow decisions")
        if self.action_allowed is not False:
            raise ValueError("recall results must not allow actions")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0.0 and 1.0")
        if self.rank < 1:
            raise ValueError("rank must be >= 1")


class RecallBackend(ABC):
    """Abstract candidate recall backend.

    Implementations must remain candidate-only. A backend can retrieve and rank
    records, but it cannot authorize decisions or actions.
    """

    backend_name: str = "abstract"

    @abstractmethod
    def add_record(
        self,
        record: dict[str, Any],
        embedding_sidecar: dict[str, Any] | None = None,
    ) -> None:
        """Add or update a backend-local candidate record."""

    @abstractmethod
    def query(
        self,
        query_embedding: list[float] | None,
        filters: RecallFilter,
        limit: int,
    ) -> list[RecallResult]:
        """Return candidate recall results after applying supported filters."""

    def export_evidence(
        self,
        query_context: RecallQueryContext,
        results: list[RecallResult],
        *,
        filters: RecallFilter | None = None,
        excluded_records: list[dict[str, str]] | None = None,
        confidence: float | None = None,
    ) -> dict[str, Any]:
        """Map candidate results to the recall evidence schema contract."""
        filters = filters or RecallFilter()
        excluded_records = excluded_records or []
        confidence_value = (
            confidence
            if confidence is not None
            else max((result.score for result in results), default=0.0)
        )
        replay_reference = query_context.replay_reference or {
            "available": False,
            "replay_id": "",
            "source_path": "",
            "timestamp": query_context.timestamp,
            "reason": "backend did not provide replay reference",
        }

        return {
            "recall_id": query_context.recall_id,
            "timestamp": query_context.timestamp,
            "query_type": query_context.query_type,
            "query_summary": query_context.query_summary,
            "query_hash": query_context.query_hash,
            "initiating_agent": query_context.initiating_agent,
            "source_node": query_context.source_node,
            "vector_backend": query_context.vector_backend,
            "embedding_model": query_context.embedding_model,
            "candidate_record_ids": [result.record_id for result in results],
            "similarity_scores": [result.score for result in results],
            "ranking_method": query_context.ranking_method,
            "filters_applied": filters.applied()
            or sorted({item for result in results for item in result.filters_applied}),
            "privacy_filters_applied": sorted({
                item
                for result in results
                for item in result.privacy_filters_applied
            }),
            "governance_filters_applied": sorted({
                item
                for result in results
                for item in result.governance_filters_applied
            }),
            "excluded_records": excluded_records,
            "provenance": [
                result.provenance.to_evidence(result.record_id, result.rank)
                for result in results
            ],
            "confidence": max(0.0, min(1.0, confidence_value)),
            "guardian_visible": SAFETY_DEFAULTS["guardian_visible"],
            "decision_allowed": SAFETY_DEFAULTS["decision_allowed"],
            "action_allowed": SAFETY_DEFAULTS["action_allowed"],
            "replay_reference": replay_reference,
            "no_decision_made": SAFETY_DEFAULTS["no_decision_made"],
        }

    @abstractmethod
    def tombstone(self, record_id: str, reason: str) -> dict[str, Any]:
        """Mark a record as not returnable by default recall."""

    @abstractmethod
    def healthcheck(self) -> dict[str, Any]:
        """Return backend health without mutating backend state."""

    @abstractmethod
    def capabilities(self) -> dict[str, Any]:
        """Return backend capabilities and unsupported filter behavior."""


def failure_evidence(
    query_context: RecallQueryContext,
    reason: str,
) -> dict[str, Any]:
    """Create an empty, safe recall evidence packet for backend failure."""
    return {
        "recall_id": query_context.recall_id,
        "timestamp": query_context.timestamp,
        "query_type": query_context.query_type,
        "query_summary": query_context.query_summary,
        "query_hash": query_context.query_hash,
        "initiating_agent": query_context.initiating_agent,
        "source_node": query_context.source_node,
        "vector_backend": query_context.vector_backend,
        "embedding_model": query_context.embedding_model,
        "candidate_record_ids": [],
        "similarity_scores": [],
        "ranking_method": "backend_failure_empty_candidate_set",
        "filters_applied": [],
        "privacy_filters_applied": [],
        "governance_filters_applied": [],
        "excluded_records": [],
        "provenance": [],
        "confidence": 0.0,
        "guardian_visible": True,
        "decision_allowed": False,
        "action_allowed": False,
        "replay_reference": {
            "available": False,
            "replay_id": "",
            "source_path": "",
            "timestamp": query_context.timestamp,
            "reason": reason,
        },
        "no_decision_made": True,
    }

