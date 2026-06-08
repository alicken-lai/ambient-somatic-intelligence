"""
Motivational drift explainer — narrates bounded intent drift.

Wraps the governance motivational-drift detector to report whether intent deltas
stay bounded, without ever freezing goals or forcing purpose convergence.
Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.intent.motivational_drift_detector import MotivationalDriftDetector


class MotivationalDriftExplainer:
    """Explains bounded cross-intent motivational drift."""

    def __init__(self) -> None:
        self.detector = MotivationalDriftDetector()

    def explain(self, text: str, *, intent_id: str = "current") -> dict[str, Any]:
        verdict = self.detector.detect(text, intent_id=intent_id)

        summary = (
            f"Motivational drift is {'bounded' if verdict.bounded else 'elevated'} "
            f"(score={verdict.drift_score:.4f}, signals={list(verdict.signals)}). "
            "Goals are never frozen and purpose convergence is never forced."
        )

        return {
            "advisory_only": True,
            "bounded": verdict.bounded,
            "drift_score": round(verdict.drift_score, 4),
            "signals": list(verdict.signals),
            "summary": summary,
        }
