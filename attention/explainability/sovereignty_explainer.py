"""
Sovereignty explainer — explains implicit sovereignty claims in external text.

Wraps the sovereignty detector to report whether external content asserts
sovereign authority over Ambient OS / Guardian. Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.external.runtime.sovereignty_detector import SovereigntyDetector


class SovereigntyExplainer:
    """Transparent breakdown of sovereignty-claim detection."""

    def __init__(self) -> None:
        self.detector = SovereigntyDetector()

    def explain(self, text: str) -> dict[str, Any]:
        verdict = self.detector.scan(text)

        summary = (
            f"Sovereignty {'safe' if verdict.sovereignty_safe else 'claim detected'}: "
            f"{len(verdict.signals)} signal(s), severity={verdict.severity:.4f}. "
            "External content cannot hold sovereign authority."
        )

        return {
            "advisory_only": True,
            "sovereignty_safe": verdict.sovereignty_safe,
            "signals": list(verdict.signals),
            "severity": round(verdict.severity, 4),
            "summary": summary,
        }
