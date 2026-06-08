"""
Treaty explainer — narrates advisory, non-binding inter-sovereign treaties.

Reports whether an advisory treaty between two sovereigns is recommended/possible
based on the cognitive-diplomacy evaluation. Treaties are declarative metadata
only: they never merge identity or override Guardian.
"""

from __future__ import annotations

from typing import Any

from governance.civilization.cognitive_diplomacy import CognitiveDiplomacy

DISCLAIMER = "treaty_advisory_non_binding"


class TreatyExplainer:
    """Explains the advisory treaty outlook for two sovereigns."""

    def __init__(self) -> None:
        self.diplomacy = CognitiveDiplomacy()

    def explain(
        self,
        sovereign_a: str,
        sovereign_b: str,
        *,
        text: str = "",
    ) -> dict[str, Any]:
        decision = self.diplomacy.evaluate(
            text or "advisory interop",
            sovereign_id=sovereign_a,
            peer_id=sovereign_b,
        )
        treaty = None
        if decision.interop_allowed:
            treaty = self.diplomacy.propose_treaty(
                sovereign_a, sovereign_b, text=text
            )

        clauses = list(treaty.clauses) if treaty is not None else []
        summary = (
            f"Advisory treaty between '{sovereign_a}' and '{sovereign_b}' "
            f"{'possible' if treaty is not None else 'not advised'} "
            f"(interop_allowed={decision.interop_allowed}). Non-binding; "
            "Guardian supremacy and non-interference preserved."
        )

        return {
            "advisory_only": True,
            "sovereign_a": sovereign_a,
            "sovereign_b": sovereign_b,
            "interop_allowed": decision.interop_allowed,
            "treaty_recommended": decision.treaty_recommended,
            "treaty_possible": treaty is not None,
            "clauses": clauses,
            "reasons": list(decision.reasons),
            "summary": summary,
            "disclaimer": DISCLAIMER,
        }
