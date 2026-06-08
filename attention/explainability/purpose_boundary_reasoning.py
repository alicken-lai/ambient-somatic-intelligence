"""
Purpose boundary reasoning — explains bounded civilization purpose.

Wraps the governance purpose-boundary check to report whether purpose text stays
within constitutional bounds (no autonomous purpose generation, synthetic
teleology, or centralized purpose authority). Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.purpose.purpose_boundary import PurposeBoundary


class PurposeBoundaryReasoning:
    """Explains purpose-boundary safety in human-readable terms."""

    def __init__(self) -> None:
        self.boundary = PurposeBoundary()

    def explain(self, text: str, *, scope: str = "advisory") -> dict[str, Any]:
        verdict = self.boundary.evaluate(text, scope=scope)

        summary = (
            f"Purpose boundary is {'safe' if verdict.boundary_safe else 'violated'} "
            f"({len(verdict.violations)} violation(s)). No autonomous purpose "
            "generation, synthetic teleology, or centralized purpose authority."
        )

        return {
            "advisory_only": True,
            "bounded": verdict.boundary_safe,
            "boundary_safe": verdict.boundary_safe,
            "violations": list(verdict.violations),
            "summary": summary,
        }
