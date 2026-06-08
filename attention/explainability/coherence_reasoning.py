"""
Coherence reasoning — deterministic explanation of a decision's coherence.

Surfaces the cross-layer coherence score and any damping reasons attached to a
GovernanceDecision. Deterministic: the same decision yields the same summary.
Advisory only; coherence is not a consciousness claim.
"""

from __future__ import annotations

from typing import Any


class CoherenceReasoning:
    """Explains the coherence facet of a governance decision."""

    def explain_decision(self, decision: Any) -> dict[str, Any]:
        coherent = bool(getattr(decision, "coherence_ok", True))
        score = float(getattr(decision, "coherence_score", 1.0))
        verdict = getattr(decision, "coherence_verdict", None)

        reasons: list[str] = []
        if isinstance(verdict, dict):
            reasons = [str(r) for r in verdict.get("reasons", []) or []]

        state = "held" if coherent else "damped"
        summary = (
            f"Coherence {state} (coherence_score={score:.4f}"
            + (f", reasons={reasons}" if reasons else "")
            + "). Advisory cross-layer consistency, not a consciousness claim."
        )

        return {
            "advisory_only": True,
            "coherent": coherent,
            "coherence_score": round(score, 4),
            "reasons": reasons,
            "coherence_verdict": verdict,
            "summary": summary,
        }
