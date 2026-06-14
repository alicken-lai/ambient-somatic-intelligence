"""Multi-stage verification pipeline."""

from __future__ import annotations

import hashlib
from typing import Any

from hermes.verification.claims import Claim, ClaimExtractor
from hermes.verification.contradiction_detector import detect_contradiction
from hermes.verification.evidence import Evidence
from hermes.verification.evidence_scoring import evidence_score
from hermes.verification.verification_discipline import verification_requirement


class VerificationPipeline:
    def __init__(self, extractor: ClaimExtractor | None = None):
        self.extractor = extractor or ClaimExtractor()

    def run(self, artifact: Any, *, source: str = "artifact", evidence: list[Evidence] | None = None, guardian_status: str | None = None) -> dict[str, Any]:
        claims = self.extractor.extract(artifact, source=source)
        evidence = evidence or []
        statuses: dict[str, str] = {}
        contradictions: list[dict[str, Any]] = []
        verified: list[dict[str, Any]] = []
        unsupported: list[dict[str, Any]] = []
        contradicted: list[dict[str, Any]] = []
        for claim in claims:
            related = [item for item in evidence if claim.claim_id in item.supports_claims or _text_match(claim, item)]
            contradiction = next((detect_contradiction(claim, item, guardian_status=guardian_status) for item in related if detect_contradiction(claim, item, guardian_status=guardian_status)["contradiction"]), None)
            if contradiction is None:
                contradiction = detect_contradiction(claim, guardian_status=guardian_status)
            contradictions.append({"claim_id": claim.claim_id, **contradiction})
            if contradiction["contradiction"]:
                statuses[claim.claim_id] = "contradicted"
                contradicted.append(claim.to_dict())
            elif related:
                statuses[claim.claim_id] = "verified"
                verified.append(claim.to_dict())
            elif verification_requirement(claim)["required"]:
                statuses[claim.claim_id] = "unsupported"
                unsupported.append(claim.to_dict())
            else:
                statuses[claim.claim_id] = "pending"
        score = evidence_score(claims, evidence, statuses, contradictions)
        return {
            "claims": [claim.to_dict() for claim in claims],
            "verified": verified,
            "unsupported": unsupported,
            "contradicted": contradicted,
            "statuses": statuses,
            "contradictions": contradictions,
            "confidence": round(score / 100.0, 4),
            "evidence_score": score,
        }


def evidence_for_claim(claim: Claim, source_type: str, source_reference: str, confidence: float = 0.8) -> Evidence:
    digest = hashlib.sha256(f"{claim.claim_id}:{source_reference}".encode("utf-8")).hexdigest()[:16]
    return Evidence(f"evidence-{digest}", source_type, source_reference, confidence, [claim.claim_id])


def _text_match(claim: Claim, evidence: Evidence) -> bool:
    claim_terms = {word for word in claim.claim_text.lower().split() if len(word) > 4}
    evidence_terms = set(evidence.source_reference.lower().split())
    return len(claim_terms.intersection(evidence_terms)) >= 3
