"""Unified confidence lifecycle model with audit trail."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .decay_rules import DecayRule


@dataclass
class ConfidenceUpdate:
    entry_id: str
    previous_confidence: float
    new_confidence: float
    reason: str
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "previous_confidence": self.previous_confidence,
            "new_confidence": self.new_confidence,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConfidenceUpdate:
        return cls(
            entry_id=data["entry_id"],
            previous_confidence=data["previous_confidence"],
            new_confidence=data["new_confidence"],
            reason=data["reason"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


class ConfidenceHistory:
    """Append-only audit trail of all confidence changes."""

    def __init__(self) -> None:
        self._updates: list[ConfidenceUpdate] = []

    def append(self, update: ConfidenceUpdate) -> None:
        self._updates.append(update)

    def get_history(self, entry_id: str | None = None) -> list[ConfidenceUpdate]:
        if entry_id is None:
            return list(self._updates)
        return [u for u in self._updates if u.entry_id == entry_id]

    def __len__(self) -> int:
        return len(self._updates)

    def to_list(self) -> list[dict[str, Any]]:
        return [u.to_dict() for u in self._updates]


class ConfidenceModel:
    """Central authority for all confidence mutations."""

    def __init__(self) -> None:
        self.history = ConfidenceHistory()

    def _clamp(self, value: float, floor: float = 0.0, ceiling: float = 0.99) -> float:
        return max(floor, min(ceiling, value))

    def _make_update(
        self,
        entry: Any,
        new_confidence: float,
        reason: str,
        floor: float = 0.0,
    ) -> ConfidenceUpdate:
        clamped = self._clamp(new_confidence, floor=floor)
        update = ConfidenceUpdate(
            entry_id=entry.entry_id,
            previous_confidence=entry.confidence,
            new_confidence=clamped,
            reason=reason,
            timestamp=datetime.now(timezone.utc),
        )
        entry.confidence = clamped
        self.history.append(update)
        return update

    def update_on_success(self, entry: Any, context: str = "") -> ConfidenceUpdate:
        new_conf = entry.confidence + 0.05 * (1.0 - entry.confidence)
        return self._make_update(entry, new_conf, "reuse_success")

    def update_on_failure(
        self, entry: Any, context: str = "", rule: DecayRule | None = None
    ) -> ConfidenceUpdate:
        floor = rule.min_confidence if rule else 0.0
        new_conf = entry.confidence - 0.1 * entry.confidence
        return self._make_update(entry, new_conf, "reuse_failure", floor=floor)

    def update_on_contradiction(
        self, entry: Any, evidence: str = "", rule: DecayRule | None = None
    ) -> ConfidenceUpdate:
        penalty = rule.contradiction_penalty if rule else 0.1
        floor = rule.min_confidence if rule else 0.0
        new_conf = entry.confidence - penalty
        if hasattr(entry, "apply_contradiction") and callable(
            entry.apply_contradiction
        ):
            entry.apply_contradiction()
        return self._make_update(entry, new_conf, "contradiction", floor=floor)

    def update_on_access(self, entry: Any) -> ConfidenceUpdate:
        new_conf = entry.confidence + 0.01 * (1.0 - entry.confidence)
        return self._make_update(entry, new_conf, "validation")

    def apply_decay(
        self, entry: Any, elapsed_days: float, rule: DecayRule
    ) -> ConfidenceUpdate:
        new_conf = entry.confidence * math.exp(-rule.base_rate_per_day * elapsed_days)
        return self._make_update(entry, new_conf, "decay", floor=rule.min_confidence)
