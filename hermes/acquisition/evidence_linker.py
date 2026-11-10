"""Link claims and knowledge assets to evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hermes.acquisition.evidence_collector import CandidateEvidence
from hermes.verification.claims import Claim


@dataclass(frozen=True)
class EvidenceLink:
    claim_id: str
    evidence_id: str
    support_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "evidence_id": self.evidence_id,
            "support_score": self.support_score,
        }


class EvidenceLinker:
    def link(self, claim: Claim, candidates: list[CandidateEvidence], *, threshold: float = 0.05) -> list[EvidenceLink]:
        return [
            EvidenceLink(claim.claim_id, candidate.evidence.evidence_id, candidate.relevance_score)
            for candidate in candidates
            if candidate.relevance_score >= threshold
        ]
