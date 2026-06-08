"""
Metacognitive reasoning — explains the meta-assessment of a decision.

Surfaces the bounded metacognition score and reflection state attached to a
GovernanceDecision. Observational only: metacognition reflects on cognition,
it does not override governance and makes no consciousness claim.
"""

from __future__ import annotations

from typing import Any

DISCLAIMER = "metacognitive_advisory_not_consciousness_claim"


class MetacognitiveReasoning:
    """Explains the metacognitive facet of a governance decision."""

    def explain_decision(self, decision: Any) -> dict[str, Any]:
        reflective = bool(getattr(decision, "metacognitive_reflective", True))
        score = float(getattr(decision, "metacognition_score", 1.0))
        verdict = getattr(decision, "metacognitive_verdict", None)

        reasons: list[str] = []
        if isinstance(verdict, dict):
            reasons = [str(r) for r in verdict.get("reasons", []) or []]

        state = "reflective" if reflective else "non_reflective"
        summary = (
            f"Metacognition is {state} (metacognition_score={score:.4f}"
            + (f", reasons={reasons}" if reasons else "")
            + "). Observational meta-assessment; never overrides governance."
        )

        return {
            "advisory_only": True,
            "reflective": reflective,
            "metacognition_score": round(score, 4),
            "reasons": reasons,
            "metacognitive_verdict": verdict,
            "summary": summary,
            "disclaimer": DISCLAIMER,
        }
