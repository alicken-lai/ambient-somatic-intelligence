"""
Intent continuity reasoning — explains advisory cross-epoch motivational continuity.

Wraps the governance intent-continuity evaluator to narrate whether civilization
intent can be advisorily coordinated across epochs. Observational only: purpose
convergence is never forced, goals are never frozen, and Guardian is never weakened.
"""

from __future__ import annotations

from typing import Any

from governance.intent.intent_continuity import IntentContinuity


class IntentContinuityReasoning:
    """Explains an intent-continuity evaluation in human-readable terms."""

    def __init__(self) -> None:
        self.continuity = IntentContinuity()

    def explain(
        self,
        text: str,
        *,
        intent_id: str = "current",
        runtime_id: str = "ambient",
    ) -> dict[str, Any]:
        verdict = self.continuity.evaluate(
            text, intent_id=intent_id, runtime_id=runtime_id
        )
        result = verdict.to_dict()

        verb = "continuous" if verdict.continuous else "fragmented"
        summary = (
            f"Advisory intent continuity is {verb} for intent '{intent_id}' "
            f"(reasons={list(verdict.reasons)}). No forced purpose convergence or "
            "frozen goals; Guardian supremacy preserved."
        )
        result["advisory_only"] = True
        result["summary"] = summary
        return result
