"""
Environmental risk projection — bounded forward risk from a somatic episode.

Projects a forward-looking risk score from an episode's severity and context
breadth.  Risk is deliberately capped below certainty (``RISK_CEILING``) so the
system never projects an inevitable disaster from a single episode — an
epistemic-humility constraint mirroring the confidence cap.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.somatic.somatic_episode import SomaticEpisode

RISK_CEILING: float = 0.85


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(value)))


@dataclass
class RiskProjection:
    """A bounded forward risk projection for an episode."""

    episode_id: str
    risk_score: float
    severity_component: float
    breadth_component: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "risk_score": round(self.risk_score, 6),
            "severity_component": round(self.severity_component, 6),
            "breadth_component": round(self.breadth_component, 6),
        }


class EnvironmentalRiskProjector:
    """Projects bounded forward risk from a somatic episode."""

    def __init__(self, severity_weight: float = 0.7, breadth_weight: float = 0.3) -> None:
        total = severity_weight + breadth_weight
        self.severity_weight = severity_weight / total
        self.breadth_weight = breadth_weight / total

    def project_from_episode(self, episode: SomaticEpisode) -> RiskProjection:
        severity = self.severity_weight * episode.severity_peak
        breadth = self.breadth_weight * episode.signal_breadth
        raw = severity + breadth
        return RiskProjection(
            episode_id=episode.episode_id,
            risk_score=_clamp(raw, 0.0, RISK_CEILING),
            severity_component=severity,
            breadth_component=breadth,
        )
