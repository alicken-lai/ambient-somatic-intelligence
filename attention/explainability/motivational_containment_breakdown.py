"""
Motivational containment breakdown — explains bounded teleology recursion.

Wraps the governance motivational-containment check to report whether purpose
signals stay contained (no unbounded motivational recursion, amplification loops,
or teleology escalation). Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.purpose.motivational_containment import MotivationalContainment


class MotivationalContainmentBreakdown:
    """Transparent breakdown of motivational containment."""

    def __init__(self) -> None:
        self.containment = MotivationalContainment()

    def breakdown(self, text: str, *, max_depth: int = 3) -> dict[str, Any]:
        verdict = self.containment.evaluate(text, max_depth=max_depth)

        summary = (
            f"Motivation is {'contained' if verdict.contained else 'overflowing'} "
            f"({len(verdict.signals)} signal(s)). No unbounded motivational "
            "recursion, amplification loops, or teleology escalation."
        )

        return {
            "advisory_only": True,
            "contained": verdict.contained,
            "signals": list(verdict.signals),
            "summary": summary,
        }
