"""Reuse existing evidence for similar claims."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hermes.acquisition.knowledge_index.index import _terms
from hermes.verification.claims import Claim
from hermes.verification.evidence import Evidence


@dataclass(frozen=True)
class ReuseResult:
    evidence: list[Evidence]
    reuse_frequency: int
    reuse_success: bool
    reuse_confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence": [item.to_dict() for item in self.evidence],
            "reuse_frequency": self.reuse_frequency,
            "reuse_success": self.reuse_success,
            "reuse_confidence": self.reuse_confidence,
        }


class KnowledgeReuseEngine:
    def reuse(self, claim: Claim, existing_evidence: list[Evidence]) -> ReuseResult:
        claim_terms = _terms(claim.claim_text)
        matches = []
        for evidence in existing_evidence:
            evidence_terms = _terms(evidence.source_reference)
            overlap = len(claim_terms.intersection(evidence_terms)) / max(1, len(claim_terms))
            if overlap >= 0.25:
                matches.append(evidence)
        confidence = min(1.0, sum(item.confidence for item in matches) / max(1, len(matches)))
        return ReuseResult(matches, len(matches), bool(matches), round(confidence, 4))
