"""
Identity reasoning — deterministic explanation of a decision's identity outcome.

Surfaces the cognition origin and bounded identity authority embedded in a
GovernanceDecision. Deterministic: the same decision always yields the same
explanation (no timestamps or volatile fields enter the summary).
"""

from __future__ import annotations

from typing import Any


class IdentityReasoning:
    """Explains the identity/provenance facet of a governance decision."""

    def explain_decision(self, decision: Any) -> dict[str, Any]:
        provenance = getattr(decision, "provenance", None)
        if isinstance(provenance, dict):
            origin = str(provenance.get("origin", "unknown"))
        else:
            origin = "unknown"

        trusted = bool(getattr(decision, "identity_trusted", True))
        multiplier = float(getattr(decision, "identity_authority_multiplier", 1.0))

        summary = (
            f"Cognition origin={origin}, trusted={trusted}, "
            f"authority_multiplier={multiplier:.4f}. "
            "Advisory identity assessment; bounded and non-ontological."
        )

        return {
            "advisory_only": True,
            "origin": origin,
            "trusted": trusted,
            "authority_multiplier": round(multiplier, 4),
            "summary": summary,
        }
