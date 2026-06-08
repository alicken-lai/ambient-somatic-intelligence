"""
Homeostasis reasoning — explains the homeostatic outcome of a decision.

Surfaces the bounded homeostasis score and stabilization recommendations
attached to a GovernanceDecision. Observational only: recommendations never
override governance or execute autonomously.
"""

from __future__ import annotations

from typing import Any

DISCLAIMER = "homeostasis_advisory_not_autonomous_execution"


class HomeostasisReasoning:
    """Explains the homeostasis facet of a governance decision."""

    def explain_decision(self, decision: Any) -> dict[str, Any]:
        stable = bool(getattr(decision, "homeostasis_stable", True))
        score = float(getattr(decision, "homeostasis_score", 1.0))
        verdict = getattr(decision, "homeostasis_verdict", None)
        recommendations = [
            str(r) for r in getattr(decision, "stabilization_recommendations", []) or []
        ]

        state = "stable" if stable else "stabilizing"
        summary = (
            f"Cognition is {state} (homeostasis_score={score:.4f}) with "
            f"{len(recommendations)} advisory recommendation(s). "
            "Observational stabilization; never overrides governance."
        )

        return {
            "advisory_only": True,
            "stable": stable,
            "homeostasis_score": round(score, 4),
            "recommendations": recommendations,
            "homeostasis_verdict": verdict,
            "summary": summary,
            "disclaimer": DISCLAIMER,
        }
