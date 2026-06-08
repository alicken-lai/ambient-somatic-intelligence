"""
Cognition containment breakdown — explains bounded cognitive recursion.

Wraps the governance cognition-containment check to report whether agency signals
stay contained (no unbounded cognitive recursion, agency amplification loops, or
selfhood escalation). Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.agency.cognition_containment import CognitionContainment


class CognitionContainmentBreakdown:
    """Transparent breakdown of cognition containment."""

    def __init__(self) -> None:
        self.containment = CognitionContainment()

    def breakdown(self, text: str, *, max_depth: int = 3) -> dict[str, Any]:
        verdict = self.containment.evaluate(text, max_depth=max_depth)

        summary = (
            f"Cognition is {'contained' if verdict.contained else 'overflowing'} "
            f"({len(verdict.signals)} signal(s)). No unbounded cognitive "
            "recursion, agency amplification loops, or selfhood escalation."
        )

        return {
            "advisory_only": True,
            "contained": verdict.contained,
            "signals": list(verdict.signals),
            "summary": summary,
        }
