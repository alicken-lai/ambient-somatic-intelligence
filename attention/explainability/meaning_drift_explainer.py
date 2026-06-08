"""
Meaning drift explainer — narrates bounded interpretive drift.

Wraps the governance meaning-drift detector to report whether interpretive deltas
stay bounded, without ever freezing meaning or forcing symbolic sync.
Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.meaning.meaning_drift_detector import MeaningDriftDetector


class MeaningDriftExplainer:
    """Explains bounded cross-concept meaning drift."""

    def __init__(self) -> None:
        self.detector = MeaningDriftDetector()

    def explain(self, text: str, *, concept_id: str = "current") -> dict[str, Any]:
        verdict = self.detector.detect(text, concept_id=concept_id)

        summary = (
            f"Meaning drift is {'bounded' if verdict.bounded else 'elevated'} "
            f"(score={verdict.drift_score:.4f}, signals={list(verdict.signals)}). "
            "Meaning is never frozen and symbolic sync is never forced."
        )

        return {
            "advisory_only": True,
            "bounded": verdict.bounded,
            "drift_score": round(verdict.drift_score, 4),
            "signals": list(verdict.signals),
            "summary": summary,
        }
