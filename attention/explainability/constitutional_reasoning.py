"""
Constitutional reasoning — explains the constitutional verdict of a decision.

Surfaces, in plain terms, whether a governance decision was blocked by the
frozen constitution (guardian supremacy, epistemic limit, replay boundary,
forecast boundary, self-modification, no recursive governance) before any
arbitration took place. Strictly advisory and transparent.
"""

from __future__ import annotations

from typing import Any


class ConstitutionalReasoning:
    """Narrates the constitutional outcome embedded in a GovernanceDecision."""

    def explain_decision(self, decision: Any) -> dict[str, Any]:
        compliant = bool(getattr(decision, "constitutional_compliant", True))
        blocked = bool(getattr(decision, "constitutional_blocked", False))
        accepted = bool(getattr(decision, "accepted", False))
        reason = str(getattr(decision, "reason", "ok"))
        verdict = getattr(decision, "constitutional_verdict", None)

        violations: list[str] = []
        if isinstance(verdict, dict):
            for v in verdict.get("violations", []) or []:
                if isinstance(v, dict):
                    violations.append(str(v.get("rule_id", "unknown")))
                else:
                    violations.append(str(v))

        if blocked:
            summary = (
                "Constitution blocked this proposal before arbitration "
                f"(reason={reason}"
                + (f", violations={violations}" if violations else "")
                + ")."
            )
        else:
            summary = "Constitution found no violation; proposal passed to arbitration."

        return {
            "advisory_only": True,
            "constitutional_compliant": compliant,
            "constitutional_blocked": blocked,
            "accepted": accepted,
            "reason": reason,
            "violations": violations,
            "constitutional_verdict": verdict,
            "summary": summary,
        }
