"""
Somatic episode — a consolidated record of a somatic attention event.

A :class:`SomaticEpisode` captures the signal types that co-occurred during a
somatic disturbance, the peak severity reached, and the environmental
signature (ambient context) under which it happened.  Episodes feed resonance,
risk projection, and confidence calibration.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SomaticEpisode:
    """A single consolidated somatic episode."""

    signal_types: list[str] = field(default_factory=list)
    severity_peak: float = 0.0
    environmental_signature: dict[str, Any] = field(default_factory=dict)
    episode_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: str = field(default_factory=_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.severity_peak = _clamp_unit(self.severity_peak)

    @property
    def signature_richness(self) -> float:
        """How rich the environmental context is, normalised to ``[0, 1]``."""
        if not self.environmental_signature:
            return 0.0
        return min(1.0, len(self.environmental_signature) / 3.0)

    @property
    def signal_breadth(self) -> float:
        """How many distinct signal types participated, normalised to ``[0, 1]``."""
        if not self.signal_types:
            return 0.0
        return min(1.0, len(set(self.signal_types)) / 3.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "signal_types": list(self.signal_types),
            "severity_peak": round(self.severity_peak, 6),
            "environmental_signature": dict(self.environmental_signature),
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }
