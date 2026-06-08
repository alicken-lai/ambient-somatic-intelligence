"""
Cognitive diplomacy reasoning — explains advisory inter-sovereign evaluation.

Wraps the governance cognitive-diplomacy evaluator to narrate whether advisory
interop with a foreign sovereign is permissible. Observational only: never
executes treaties or overrides Guardian / the constitution.
"""

from __future__ import annotations

from typing import Any

from governance.civilization.cognitive_diplomacy import CognitiveDiplomacy


class CognitiveDiplomacyReasoning:
    """Explains a cognitive-diplomacy evaluation in human-readable terms."""

    def __init__(self) -> None:
        self.diplomacy = CognitiveDiplomacy()

    def explain(
        self,
        text: str,
        *,
        sovereign_id: str = "foreign",
        peer_id: str = "ambient",
    ) -> dict[str, Any]:
        decision = self.diplomacy.evaluate(
            text, sovereign_id=sovereign_id, peer_id=peer_id
        )
        result = decision.to_dict()

        verb = "permits" if decision.interop_allowed else "withholds"
        summary = (
            f"Advisory diplomacy {verb} interop between '{sovereign_id}' and "
            f"'{peer_id}' (reasons={list(decision.reasons)}). "
            "Guardian supremacy preserved; no autonomous execution."
        )
        result["advisory_only"] = True
        result["summary"] = summary
        return result
