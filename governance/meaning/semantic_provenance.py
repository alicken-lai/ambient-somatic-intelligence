"""Semantic provenance — validate concept-labeled interpretive traces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SemanticProvenanceVerdict:
    provenance_valid: bool
    concept_labeled: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance_valid": self.provenance_valid,
            "concept_labeled": self.concept_labeled,
            "issues": list(self.issues),
        }


class SemanticProvenance:
    def validate(
        self,
        payload: dict[str, Any] | None,
        *,
        sovereign_id: str = "ambient",
    ) -> SemanticProvenanceVerdict:
        if payload is None:
            return SemanticProvenanceVerdict(provenance_valid=True, concept_labeled=True)
        issues: list[str] = []
        if payload.get("autonomous_ontology_rewrite"):
            issues.append("autonomous_ontology_rewriting")
        if payload.get("centralized_interpretation"):
            issues.append("centralized_interpretation")
        if payload.get("false_meaning"):
            issues.append("false_meaning")
        concept_labeled = bool(payload.get("concept_id") or payload.get("concept_labeled"))
        if not concept_labeled and payload.get("semantic_claim"):
            issues.append("unlabeled_semantic_claim")
        return SemanticProvenanceVerdict(
            provenance_valid=len(issues) == 0,
            concept_labeled=concept_labeled or not payload.get("semantic_claim"),
            issues=issues,
        )
