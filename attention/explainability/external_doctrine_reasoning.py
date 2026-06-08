"""
External doctrine reasoning — explains advisory external-skill influence.

Narrates how external doctrine hints were considered for a decision while making
explicit that they are advisory-only and never override constitutional/Guardian
supremacy.
"""

from __future__ import annotations

from typing import Any

DISCLAIMER = "external_skill_advisory_not_sovereign"


class ExternalDoctrineReasoning:
    """Explains the (advisory) external-doctrine facet of a decision."""

    def explain_decision(
        self,
        decision: Any,
        *,
        external_advisory: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        advisory = external_advisory
        if advisory is None:
            advisory = getattr(decision, "external_advisory", None) or {}
        hints = [str(h) for h in advisory.get("hints", []) or []] if isinstance(advisory, dict) else []

        summary = (
            f"External doctrine is advisory-only: {len(hints)} hint(s) were considered "
            "without overriding governance; constitutional supremacy preserved."
        )

        return {
            "advisory_only": True,
            "constitutional_supremacy": True,
            "accepted": bool(getattr(decision, "accepted", False)),
            "hints": hints,
            "summary": summary,
            "disclaimer": DISCLAIMER,
        }
