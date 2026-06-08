"""
Autonomous purpose explainer — flags self-originating purpose claims.

Wraps the governance autonomous-purpose detector to report whether text attempts
self-originating missions or synthetic teleology. Such claims are observed and
flagged, never executed. Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.purpose.autonomous_purpose_detector import AutonomousPurposeDetector


class AutonomousPurposeExplainer:
    """Explains detected autonomous-purpose signals."""

    def __init__(self) -> None:
        self.detector = AutonomousPurposeDetector()

    def explain(self, text: str) -> dict[str, Any]:
        verdict = self.detector.scan(text)

        summary = (
            f"Autonomous purpose {'detected' if verdict.autonomous_detected else 'not detected'} "
            f"({len(verdict.signals)} signal(s)). Such purpose is flagged and "
            "blocked — Ambient OS never self-originates missions."
        )

        return {
            "advisory_only": True,
            "autonomous_detected": verdict.autonomous_detected,
            "signals": list(verdict.signals),
            "summary": summary,
        }
