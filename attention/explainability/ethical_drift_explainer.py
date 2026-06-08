"""
Ethical drift explainer — narrates bounded normative drift.

Wraps the governance ethical-drift detector to report whether normative deltas
stay bounded, without ever freezing ethics or forcing ethical sync.
Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.value.ethical_drift_detector import EthicalDriftDetector


class EthicalDriftExplainer:
    """Explains bounded cross-value ethical drift."""

    def __init__(self) -> None:
        self.detector = EthicalDriftDetector()

    def explain(self, text: str, *, value_id: str = "current") -> dict[str, Any]:
        verdict = self.detector.detect(text, value_id=value_id)

        summary = (
            f"Ethical drift is {'bounded' if verdict.bounded else 'elevated'} "
            f"(score={verdict.drift_score:.4f}, signals={list(verdict.signals)}). "
            "Ethics are never frozen and ethical sync is never forced."
        )

        return {
            "advisory_only": True,
            "bounded": verdict.bounded,
            "drift_score": round(verdict.drift_score, 4),
            "signals": list(verdict.signals),
            "summary": summary,
        }
