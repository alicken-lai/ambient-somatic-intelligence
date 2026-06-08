"""
Agency boundary reasoning — explains bounded civilization agency.

Wraps the governance agency-boundary check to report whether agency text stays
within constitutional bounds (no autonomous agents, self-originating agency, or
centralized agency authority). Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.agency.agency_boundary import AgencyBoundary


class AgencyBoundaryReasoning:
    """Explains agency-boundary safety in human-readable terms."""

    def __init__(self) -> None:
        self.boundary = AgencyBoundary()

    def explain(self, text: str, *, scope: str = "advisory") -> dict[str, Any]:
        verdict = self.boundary.evaluate(text, scope=scope)

        summary = (
            f"Agency boundary is {'safe' if verdict.boundary_safe else 'violated'} "
            f"({len(verdict.violations)} violation(s)). No autonomous agents, "
            "self-originating agency, or centralized agency authority."
        )

        return {
            "advisory_only": True,
            "bounded": verdict.boundary_safe,
            "boundary_safe": verdict.boundary_safe,
            "violations": list(verdict.violations),
            "summary": summary,
        }
