"""Confidence decay rules for the memory ontology."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .layer_definition import MemoryLayer


@dataclass
class DecayRule:
    layer: MemoryLayer
    base_rate_per_day: float
    inactivity_multiplier: float
    inactivity_threshold_days: int
    contradiction_penalty: float
    min_confidence: float
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer.value,
            "base_rate_per_day": self.base_rate_per_day,
            "inactivity_multiplier": self.inactivity_multiplier,
            "inactivity_threshold_days": self.inactivity_threshold_days,
            "contradiction_penalty": self.contradiction_penalty,
            "min_confidence": self.min_confidence,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DecayRule:
        return cls(
            layer=MemoryLayer(data["layer"]),
            base_rate_per_day=data["base_rate_per_day"],
            inactivity_multiplier=data["inactivity_multiplier"],
            inactivity_threshold_days=data["inactivity_threshold_days"],
            contradiction_penalty=data["contradiction_penalty"],
            min_confidence=data["min_confidence"],
            description=data["description"],
        )


DECAY_RULES: list[DecayRule] = [
    DecayRule(
        layer=MemoryLayer.L1_EPISODIC,
        base_rate_per_day=0.1,
        inactivity_multiplier=2.0,
        inactivity_threshold_days=7,
        contradiction_penalty=0.05,
        min_confidence=0.01,
        description="Episodic memories decay fastest",
    ),
    DecayRule(
        layer=MemoryLayer.L2_INSTINCT,
        base_rate_per_day=0.03,
        inactivity_multiplier=1.5,
        inactivity_threshold_days=30,
        contradiction_penalty=0.1,
        min_confidence=0.05,
        description="Instincts decay moderately",
    ),
    DecayRule(
        layer=MemoryLayer.L3_SKILL,
        base_rate_per_day=0.01,
        inactivity_multiplier=1.3,
        inactivity_threshold_days=90,
        contradiction_penalty=0.15,
        min_confidence=0.1,
        description="Skills decay slowly",
    ),
    DecayRule(
        layer=MemoryLayer.L4_STRATEGIC,
        base_rate_per_day=0.003,
        inactivity_multiplier=1.1,
        inactivity_threshold_days=365,
        contradiction_penalty=0.2,
        min_confidence=0.2,
        description="Strategic rules decay very slowly",
    ),
]

DECAY_RULE_REGISTRY: dict[MemoryLayer, DecayRule] = {r.layer: r for r in DECAY_RULES}


def _last_access_time(entry: Any) -> datetime | None:
    for attr in ("last_accessed", "last_validated", "last_executed", "last_applied"):
        val = getattr(entry, attr, None)
        if val is not None:
            return val
    return None


def compute_decay(
    entry: Any, rule: DecayRule, current_time: datetime
) -> float:
    """Compute new confidence after time-based decay.

    Uses exponential decay: confidence *= exp(-rate * elapsed_days).
    If the entry has been inactive beyond the threshold, the rate is
    multiplied by the inactivity_multiplier.
    """
    elapsed = (current_time - entry.timestamp).total_seconds() / 86400.0
    if elapsed <= 0:
        return entry.confidence

    rate = rule.base_rate_per_day

    last_access = _last_access_time(entry)
    if last_access is not None:
        days_inactive = (current_time - last_access).total_seconds() / 86400.0
        if days_inactive > rule.inactivity_threshold_days:
            rate *= rule.inactivity_multiplier

    new_confidence = entry.confidence * math.exp(-rate * elapsed)
    return max(new_confidence, rule.min_confidence)


def should_remove(entry: Any, rule: DecayRule) -> bool:
    """Check if entry confidence has fallen to or below the minimum."""
    return entry.confidence <= rule.min_confidence
