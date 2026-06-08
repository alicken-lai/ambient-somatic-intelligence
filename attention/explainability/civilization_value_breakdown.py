"""
Civilization value breakdown — explains normative boundary safety.

Wraps the governance normative-boundary check to report whether value text stays
within constitutional bounds (no universal morality, immutable ethics, forced
sync, or centralized value authority). Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.value.normative_boundary import NormativeBoundary


class CivilizationValueBreakdown:
    """Transparent breakdown of normative-boundary safety."""

    def __init__(self) -> None:
        self.boundary = NormativeBoundary()

    def explain(self, text: str, *, scope: str = "advisory") -> dict[str, Any]:
        verdict = self.boundary.evaluate(text, scope=scope)

        summary = (
            f"Normative boundary is "
            f"{'safe' if verdict.boundary_safe else 'violated'} "
            f"({len(verdict.violations)} violation(s)). No universal morality, "
            "immutable ethics, or centralized value authority."
        )

        return {
            "advisory_only": True,
            "boundary_safe": verdict.boundary_safe,
            "violations": list(verdict.violations),
            "summary": summary,
        }
