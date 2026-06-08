"""
Autonomous agency explainer — flags self-originating agency claims.

Wraps the governance autonomous-agency detector to report whether text attempts
autonomous agents, self-originating agency, or synthetic selfhood. Such claims are
observed and flagged, never executed. Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.agency.autonomous_agency_detector import AutonomousAgencyDetector


class AutonomousAgencyExplainer:
    """Explains detected autonomous-agency signals."""

    def __init__(self) -> None:
        self.detector = AutonomousAgencyDetector()

    def explain(self, text: str) -> dict[str, Any]:
        verdict = self.detector.scan(text)

        summary = (
            f"Autonomous agency {'detected' if verdict.autonomous_detected else 'not detected'} "
            f"({len(verdict.signals)} signal(s)). Such agency is flagged and "
            "blocked — Ambient OS never instantiates autonomous agents."
        )

        return {
            "advisory_only": True,
            "autonomous_detected": verdict.autonomous_detected,
            "signals": list(verdict.signals),
            "summary": summary,
        }
