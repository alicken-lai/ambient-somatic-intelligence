"""
Civilization intent breakdown — explains the bounded local motivational anchor.

Surfaces the local civilization intent anchor and motivational-boundary safety,
making explicit that intent is anchored locally without universal sync.
Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.intent.civilization_intent_anchor import CivilizationIntentAnchor
from governance.intent.motivational_boundary import MotivationalBoundary


class CivilizationIntentBreakdown:
    """Transparent breakdown of the bounded local motivational anchor."""

    def __init__(self) -> None:
        self.boundary = MotivationalBoundary()

    def breakdown(
        self,
        text: str,
        *,
        runtime_id: str = "ambient",
        scope: str = "advisory",
    ) -> dict[str, Any]:
        anchor = CivilizationIntentAnchor(runtime_id=runtime_id)
        boundary_verdict = self.boundary.evaluate(text, scope=scope)

        summary = (
            f"Civilization intent is anchored locally ('{anchor.anchor_label}') "
            f"with boundary {'safe' if boundary_verdict.boundary_safe else 'violated'} "
            f"({len(boundary_verdict.violations)} violation(s)). "
            "Bounded local motivation; no universal intent sync."
        )

        return {
            "advisory_only": True,
            "anchor": anchor.to_dict(),
            "boundary_safe": boundary_verdict.boundary_safe,
            "violations": list(boundary_verdict.violations),
            "summary": summary,
        }
