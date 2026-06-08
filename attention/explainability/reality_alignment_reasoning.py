"""
Reality alignment reasoning — explains advisory cross-runtime truth alignment.

Wraps the governance reality-alignment evaluator to narrate whether operational
truth can be advisorily aligned across runtimes. Observational only: sovereign
realities are never merged and Guardian / the constitution is never overridden.
"""

from __future__ import annotations

from typing import Any

from governance.reality.reality_alignment import RealityAlignment


class RealityAlignmentReasoning:
    """Explains a reality-alignment evaluation in human-readable terms."""

    def __init__(self) -> None:
        self.alignment = RealityAlignment()

    def explain(
        self,
        text: str,
        *,
        left_runtime: str = "ambient",
        right_runtime: str = "foreign",
    ) -> dict[str, Any]:
        verdict = self.alignment.evaluate(
            text, left_runtime=left_runtime, right_runtime=right_runtime
        )
        result = verdict.to_dict()

        verb = "aligned" if verdict.aligned else "withheld"
        summary = (
            f"Advisory reality alignment {verb} between '{left_runtime}' and "
            f"'{right_runtime}' (reasons={list(verdict.reasons)}). "
            "No sovereign-reality merge; Guardian supremacy preserved."
        )
        result["advisory_only"] = True
        result["summary"] = summary
        return result
