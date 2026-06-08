"""
Value continuity reasoning — explains advisory cross-epoch normative continuity.

Wraps the governance value-continuity evaluator to narrate whether civilization
values can be advisorily coordinated across epochs. Observational only: ethical
sync is never forced, the constitution is never rewritten, and Guardian is never
weakened.
"""

from __future__ import annotations

from typing import Any

from governance.value.value_continuity import ValueContinuity


class ValueContinuityReasoning:
    """Explains a value-continuity evaluation in human-readable terms."""

    def __init__(self) -> None:
        self.continuity = ValueContinuity()

    def explain(
        self,
        text: str,
        *,
        value_id: str = "current",
        runtime_id: str = "ambient",
    ) -> dict[str, Any]:
        verdict = self.continuity.evaluate(
            text, value_id=value_id, runtime_id=runtime_id
        )
        result = verdict.to_dict()

        verb = "continuous" if verdict.continuous else "fragmented"
        summary = (
            f"Advisory value continuity is {verb} for value '{value_id}' "
            f"(reasons={list(verdict.reasons)}). No forced ethical sync or "
            "constitutional rewrite; Guardian supremacy preserved."
        )
        result["advisory_only"] = True
        result["summary"] = summary
        return result
