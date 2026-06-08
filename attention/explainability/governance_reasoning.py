"""
Governance reasoning — human-readable explanation of a GovernanceDecision.

Strictly advisory and transparent: it narrates *why* a decision turned out the
way it did without ever asserting deterministic authority or autonomous action.
"""

from __future__ import annotations

from typing import Any


class GovernanceReasoning:
    """Explains a cognitive governance decision in plain, bounded terms."""

    def explain_decision(self, decision: Any) -> dict[str, Any]:
        accepted = bool(getattr(decision, "accepted", False))
        governed = float(getattr(decision, "governed_salience", 0.0))
        reason = str(getattr(decision, "reason", "ok"))
        autonomous_blocked = bool(getattr(decision, "autonomous_blocked", False))
        constitutional_compliant = bool(
            getattr(decision, "constitutional_compliant", True)
        )
        arbitration = getattr(decision, "arbitration", None)
        fairness = float(getattr(arbitration, "arbitration_fairness", 0.0))

        verb = "accepted" if accepted else "rejected"
        summary = (
            f"Advisory governance {verb} the salience proposal "
            f"(governed_salience={governed:.4f}, reason={reason}). "
            "This is a probabilistic recommendation, not a deterministic command; "
            "no autonomous execution follows."
        )

        return {
            "advisory_only": True,
            "no_autonomous_execution": True,
            "accepted": accepted,
            "governed_salience": round(governed, 4),
            "reason": reason,
            "autonomous_blocked": autonomous_blocked,
            "constitutional_compliant": constitutional_compliant,
            "arbitration_fairness": round(fairness, 4),
            "summary": summary,
        }
