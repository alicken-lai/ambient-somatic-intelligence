"""Collect candidate evidence from internal knowledge sources."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from hermes.acquisition.knowledge_index import KnowledgeIndex
from hermes.verification.claims import Claim
from hermes.verification.evidence import Evidence


@dataclass(frozen=True)
class CandidateEvidence:
    evidence: Evidence
    relevance_score: float
    acquisition_trace: dict[str, Any]


class EvidenceCollector:
    def __init__(self, index: KnowledgeIndex | None = None):
        self.index = index or KnowledgeIndex().build()

    def collect(self, *, claim: Claim, task: str | None = None, playbook: str | None = None, limit: int = 5) -> list[CandidateEvidence]:
        query = " ".join(filter(None, [claim.claim_text, task, playbook]))
        candidates: list[CandidateEvidence] = []
        for item, relevance in self.index.semantic_search(query, limit=limit):
            evidence = Evidence(
                evidence_id=_evidence_id(claim.claim_id, item.reference),
                source_type=item.source_type,
                source_reference=item.reference,
                confidence=min(0.95, relevance),
                supports_claims=[claim.claim_id],
            )
            candidates.append(
                CandidateEvidence(
                    evidence=evidence,
                    relevance_score=relevance,
                    acquisition_trace={
                        "claim_id": claim.claim_id,
                        "source_id": item.source_id,
                        "source_reference": item.reference,
                        "relevance_score": relevance,
                    },
                )
            )
        return candidates


def _evidence_id(claim_id: str, reference: str) -> str:
    digest = hashlib.sha256(f"{claim_id}:{reference}".encode("utf-8")).hexdigest()[:16]
    return f"acq-evidence-{digest}"
