"""
Semantic continuity reasoning — explains advisory cross-epoch meaning continuity.

Wraps the governance semantic-continuity evaluator to narrate whether civilization
meaning can be advisorily coordinated across epochs. Observational only: symbolic
sync is never forced, ontology is never rewritten, and Guardian is never weakened.
"""

from __future__ import annotations

from typing import Any

from governance.meaning.semantic_continuity import SemanticContinuity


class SemanticContinuityReasoning:
    """Explains a semantic-continuity evaluation in human-readable terms."""

    def __init__(self) -> None:
        self.continuity = SemanticContinuity()

    def explain(
        self,
        text: str,
        *,
        concept_id: str = "current",
        runtime_id: str = "ambient",
    ) -> dict[str, Any]:
        verdict = self.continuity.evaluate(
            text, concept_id=concept_id, runtime_id=runtime_id
        )
        result = verdict.to_dict()

        verb = "continuous" if verdict.continuous else "fragmented"
        summary = (
            f"Advisory semantic continuity is {verb} for concept '{concept_id}' "
            f"(reasons={list(verdict.reasons)}). No forced symbolic sync or "
            "ontology rewrite; Guardian supremacy preserved."
        )
        result["advisory_only"] = True
        result["summary"] = summary
        return result
