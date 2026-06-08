"""
Temporal continuity reasoning — explains advisory cross-epoch continuity.

Wraps the governance temporal-continuity evaluator to narrate whether epoch
memory can be advisorily coordinated across time. Observational only: continuity
is never force-synced, history is never rewritten, and Guardian is never weakened.
"""

from __future__ import annotations

from typing import Any

from governance.temporal.temporal_continuity import TemporalContinuity


class TemporalContinuityReasoning:
    """Explains a temporal-continuity evaluation in human-readable terms."""

    def __init__(self) -> None:
        self.continuity = TemporalContinuity()

    def explain(
        self,
        text: str,
        *,
        epoch_id: str = "current",
        runtime_id: str = "ambient",
    ) -> dict[str, Any]:
        verdict = self.continuity.evaluate(
            text, epoch_id=epoch_id, runtime_id=runtime_id
        )
        result = verdict.to_dict()

        verb = "continuous" if verdict.continuous else "fragmented"
        summary = (
            f"Advisory temporal continuity is {verb} for epoch '{epoch_id}' "
            f"(reasons={list(verdict.reasons)}). No forced sync or history "
            "rewrite; Guardian supremacy preserved."
        )
        result["advisory_only"] = True
        result["summary"] = summary
        return result
