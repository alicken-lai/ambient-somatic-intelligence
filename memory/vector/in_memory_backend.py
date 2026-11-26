"""Non-production in-memory candidate recall proof harness.

This backend exists only to exercise the backend-neutral recall interface in
tests and examples. It is not a production backend, does not persist state, and
does not integrate with DMN, Guardian, Replay, runtime, or kernel behavior.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from memory.vector.base import (
    RecallBackend,
    RecallFilter,
    RecallProvenance,
    RecallResult,
)


BACKEND_NAME = "in_memory_proof_harness"


@dataclass
class _StoredRecord:
    record: dict[str, Any]
    embedding_sidecar: dict[str, Any] | None
    embedding: list[float]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (left_norm * right_norm)))


def _synthetic_embedding_from_record(record: dict[str, Any]) -> list[float]:
    text = f"{record.get('record_id', '')} {' '.join(record.get('tags', []))}"
    buckets = [0.0, 0.0, 0.0, 0.0]
    for index, char in enumerate(text.encode("utf-8")):
        buckets[index % len(buckets)] += float(char % 17) / 17.0
    norm = math.sqrt(sum(value * value for value in buckets)) or 1.0
    return [value / norm for value in buckets]


def _embedding_from_sidecar(
    record: dict[str, Any],
    embedding_sidecar: dict[str, Any] | None,
) -> list[float]:
    if embedding_sidecar:
        metadata = embedding_sidecar.get("metadata", {})
        synthetic = metadata.get("synthetic_embedding")
        if isinstance(synthetic, list) and all(
            isinstance(item, int | float) for item in synthetic
        ):
            return [float(item) for item in synthetic]
    return _synthetic_embedding_from_record(record)


class InMemoryRecallBackend(RecallBackend):
    """In-process proof backend for contract tests and examples."""

    backend_name = BACKEND_NAME

    def __init__(
        self,
        *,
        support_privacy_filters: bool = True,
        support_governance_filters: bool = True,
    ) -> None:
        self._records: dict[str, _StoredRecord] = {}
        self._tombstones: dict[str, str] = {}
        self._support_privacy_filters = support_privacy_filters
        self._support_governance_filters = support_governance_filters

    def add_record(
        self,
        record: dict[str, Any],
        embedding_sidecar: dict[str, Any] | None = None,
    ) -> None:
        record_id = str(record["record_id"])
        self._records[record_id] = _StoredRecord(
            record=dict(record),
            embedding_sidecar=dict(embedding_sidecar) if embedding_sidecar else None,
            embedding=_embedding_from_sidecar(record, embedding_sidecar),
        )

    def query(
        self,
        query_embedding: list[float] | None,
        filters: RecallFilter,
        limit: int,
    ) -> list[RecallResult]:
        if limit <= 0 or query_embedding is None:
            return []
        if filters.privacy_class and not self._support_privacy_filters:
            return []
        if filters.governance_state and not self._support_governance_filters:
            return []

        candidates: list[tuple[float, dict[str, Any], _StoredRecord]] = []
        for record_id, stored in self._records.items():
            if record_id in self._tombstones:
                continue
            if not self._record_matches_filters(stored.record, filters):
                continue
            score = _cosine_similarity(query_embedding, stored.embedding)
            candidates.append((score, {"record_id": record_id}, stored))

        candidates.sort(key=lambda item: item[0], reverse=True)
        results: list[RecallResult] = []
        for rank, (score, ids, stored) in enumerate(candidates[:limit], start=1):
            record = stored.record
            content_ref = str(record.get("content_ref", ""))
            source_path, source_line = self._split_content_ref(content_ref)
            provenance = RecallProvenance(
                source_path=source_path,
                source_line=source_line,
                content_hash=str(record.get("content_hash", "")),
                backend=self.backend_name,
            )
            results.append(
                RecallResult(
                    record_id=ids["record_id"],
                    score=round(score, 6),
                    rank=rank,
                    backend=self.backend_name,
                    embedding_model=self._embedding_model(stored),
                    provenance=provenance,
                    filters_applied=filters.applied(),
                    privacy_filters_applied=self._privacy_filters(filters),
                    governance_filters_applied=self._governance_filters(filters),
                    replay_pointer=record.get("replay_pointer", {}),
                )
            )
        return results

    def tombstone(self, record_id: str, reason: str) -> dict[str, Any]:
        self._tombstones[record_id] = reason
        return {
            "record_id": record_id,
            "reason": reason,
            "tombstoned": True,
            "backend": self.backend_name,
        }

    def healthcheck(self) -> dict[str, Any]:
        return {
            "ok": True,
            "backend": self.backend_name,
            "status": "non-production in-memory proof harness",
            "details": {
                "records": len(self._records),
                "tombstones": len(self._tombstones),
            },
        }

    def capabilities(self) -> dict[str, Any]:
        supported = ["event_type", "modality", "tags"]
        if self._support_privacy_filters:
            supported.append("privacy_class")
        if self._support_governance_filters:
            supported.append("governance_state")
        return {
            "backend": self.backend_name,
            "supported_filters": supported,
            "unsupported_filters": [
                "source_node",
                "retention_policy",
                "time_range",
            ],
            "unsupported_non_safety_filters_fail_open": True,
            "requires_embeddings": True,
            "supports_tombstones": True,
            "supports_evidence_export": True,
            "failure_behavior": "empty_candidate_set_with_failure_evidence",
            "production_default": False,
        }

    def _record_matches_filters(
        self,
        record: dict[str, Any],
        filters: RecallFilter,
    ) -> bool:
        if filters.privacy_class and record.get("privacy_class") not in filters.privacy_class:
            return False
        if (
            filters.governance_state
            and record.get("governance_state") not in filters.governance_state
        ):
            return False
        if filters.event_type and record.get("event_type") not in filters.event_type:
            return False
        if filters.modality and record.get("modality") not in filters.modality:
            return False
        if filters.tags:
            record_tags = set(str(tag) for tag in record.get("tags", []))
            if not set(filters.tags) & record_tags:
                return False
        return True

    def _embedding_model(self, stored: _StoredRecord) -> str:
        if stored.embedding_sidecar:
            return str(stored.embedding_sidecar.get("embedding_model", "synthetic"))
        return "synthetic-in-memory"

    @staticmethod
    def _privacy_filters(filters: RecallFilter) -> list[str]:
        if not filters.privacy_class:
            return []
        return [f"privacy_class={filters.privacy_class}"]

    @staticmethod
    def _governance_filters(filters: RecallFilter) -> list[str]:
        if not filters.governance_state:
            return []
        return [f"governance_state={filters.governance_state}"]

    @staticmethod
    def _split_content_ref(content_ref: str) -> tuple[str, int | None]:
        if ":" not in content_ref:
            return content_ref, None
        path, line = content_ref.rsplit(":", 1)
        try:
            return path, int(line)
        except ValueError:
            return content_ref, None
