"""
Continuity fragmentation explainer — narrates bounded cross-epoch fragmentation.

Wraps the governance fragmentation detector to report whether cross-epoch
continuity deltas stay bounded, without ever forcing epoch sync or erasing
prior epochs. Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.temporal.fragmentation_detector import FragmentationDetector


class ContinuityFragmentationExplainer:
    """Explains bounded cross-epoch continuity fragmentation."""

    def __init__(self) -> None:
        self.detector = FragmentationDetector()

    def explain(self, text: str, *, epoch_id: str = "current") -> dict[str, Any]:
        verdict = self.detector.detect(text, epoch_id=epoch_id)

        summary = (
            f"Continuity fragmentation is "
            f"{'bounded' if verdict.bounded else 'elevated'} "
            f"(score={verdict.fragmentation_score:.4f}, "
            f"signals={list(verdict.signals)}). Prior epochs are never erased "
            "and continuity is never force-synced."
        )

        return {
            "advisory_only": True,
            "bounded": verdict.bounded,
            "fragmentation_score": round(verdict.fragmentation_score, 4),
            "signals": list(verdict.signals),
            "summary": summary,
        }
