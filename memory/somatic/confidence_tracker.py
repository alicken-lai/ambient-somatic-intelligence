"""Track confidence scores for somatic entities over time.

Provides a full audit trail of every confidence change — initial
assignment, success/failure updates, time-based decay, and
contradiction penalties — so downstream governance can inspect
why an entity's confidence reached its current value.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_CONFIDENCE_CEILING = 0.99
_CONFIDENCE_FLOOR = 0.01


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(val: Any) -> datetime:
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    return _utc_now()


@dataclass
class ConfidenceEvent:
    """A single confidence-change event for an entity."""

    entity_id: str
    entity_type: str  # "episode", "fingerprint", "cluster", "precursor"
    previous_confidence: float
    new_confidence: float
    reason: str  # "initial", "success", "failure", "decay", "contradiction"
    timestamp: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "previous_confidence": round(self.previous_confidence, 6),
            "new_confidence": round(self.new_confidence, 6),
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConfidenceEvent:
        return cls(
            entity_id=data["entity_id"],
            entity_type=data["entity_type"],
            previous_confidence=float(data.get("previous_confidence", 0.0)),
            new_confidence=float(data.get("new_confidence", 0.0)),
            reason=data.get("reason", ""),
            timestamp=_parse_dt(data.get("timestamp")),
        )


def _clamp(value: float) -> float:
    return max(_CONFIDENCE_FLOOR, min(value, _CONFIDENCE_CEILING))


class SomaticConfidenceTracker:
    """Tracks and updates confidence for somatic memory entities.

    All events are persisted to a JSONL history file for auditability.
    """

    def __init__(self, history_path: str = "memory/somatic/confidence_history.jsonl"):
        self._history: list[ConfidenceEvent] = []
        self._history_path = Path(history_path)
        self._load()

    # ── Recording ─────────────────────────────────────────────────────

    def record_initial(
        self,
        entity_id: str,
        entity_type: str,
        confidence: float,
    ) -> ConfidenceEvent:
        """Record the initial confidence assignment for an entity."""
        clamped = _clamp(confidence)
        event = ConfidenceEvent(
            entity_id=entity_id,
            entity_type=entity_type,
            previous_confidence=0.0,
            new_confidence=clamped,
            reason="initial",
        )
        self._history.append(event)
        self._save()
        return event

    def record_success(
        self,
        entity_id: str,
        entity_type: str,
        current_confidence: float,
    ) -> ConfidenceEvent:
        """Increase confidence on successful use.

        Formula: conf + 0.05 * (1 - conf), capped at 0.99.
        """
        new = _clamp(current_confidence + 0.05 * (1.0 - current_confidence))
        event = ConfidenceEvent(
            entity_id=entity_id,
            entity_type=entity_type,
            previous_confidence=current_confidence,
            new_confidence=new,
            reason="success",
        )
        self._history.append(event)
        self._save()
        return event

    def record_failure(
        self,
        entity_id: str,
        entity_type: str,
        current_confidence: float,
    ) -> ConfidenceEvent:
        """Decrease confidence on failure.

        Formula: conf - 0.1 * conf, floor 0.01.
        """
        new = _clamp(current_confidence - 0.1 * current_confidence)
        event = ConfidenceEvent(
            entity_id=entity_id,
            entity_type=entity_type,
            previous_confidence=current_confidence,
            new_confidence=new,
            reason="failure",
        )
        self._history.append(event)
        self._save()
        return event

    def record_contradiction(
        self,
        entity_id: str,
        entity_type: str,
        current_confidence: float,
        penalty: float = 0.1,
    ) -> ConfidenceEvent:
        """Decrease confidence on contradiction."""
        new = _clamp(current_confidence - penalty)
        event = ConfidenceEvent(
            entity_id=entity_id,
            entity_type=entity_type,
            previous_confidence=current_confidence,
            new_confidence=new,
            reason="contradiction",
        )
        self._history.append(event)
        self._save()
        return event

    def apply_decay(
        self,
        entity_id: str,
        entity_type: str,
        current_confidence: float,
        decay_rate: float,
        elapsed_days: float,
    ) -> ConfidenceEvent:
        """Apply time-based decay.

        Formula: conf * exp(-rate * days), floor 0.01.
        """
        new = _clamp(current_confidence * math.exp(-decay_rate * elapsed_days))
        event = ConfidenceEvent(
            entity_id=entity_id,
            entity_type=entity_type,
            previous_confidence=current_confidence,
            new_confidence=new,
            reason="decay",
        )
        self._history.append(event)
        self._save()
        return event

    # ── Queries ───────────────────────────────────────────────────────

    def get_history(self, entity_id: str) -> list[ConfidenceEvent]:
        """Return all events for a given entity, in chronological order."""
        return [e for e in self._history if e.entity_id == entity_id]

    def get_current_confidence(self, entity_id: str) -> Optional[float]:
        """Return the most recent confidence value for an entity, or None."""
        for event in reversed(self._history):
            if event.entity_id == entity_id:
                return event.new_confidence
        return None

    # ── Persistence ───────────────────────────────────────────────────

    def _load(self) -> None:
        if not self._history_path.exists():
            return
        try:
            with self._history_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        self._history.append(ConfidenceEvent.from_dict(json.loads(line)))
                    except (json.JSONDecodeError, KeyError) as exc:
                        logger.warning("Skipped malformed confidence line: %s", exc)
        except OSError as exc:
            logger.error("Failed to load confidence history: %s", exc)

    def _save(self) -> None:
        self._history_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._history_path.open("w", encoding="utf-8") as fh:
                for event in self._history:
                    fh.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        except OSError as exc:
            logger.error("Failed to save confidence history: %s", exc)
