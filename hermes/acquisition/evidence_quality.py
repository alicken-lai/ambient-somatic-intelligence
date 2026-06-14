"""Evidence quality ratings."""

from __future__ import annotations

from hermes.acquisition.confidence_model import calculate_confidence
from hermes.acquisition.evidence_linker import EvidenceLink
from hermes.acquisition.sources import EvidenceSource
from hermes.verification.evidence import Evidence


def evidence_quality_rating(
    *,
    evidence: list[Evidence],
    links: list[EvidenceLink],
    sources: dict[str, EvidenceSource],
    verification_success_history: float = 0.0,
    contradiction_history: int = 0,
) -> dict[str, object]:
    confidence = calculate_confidence(
        evidence=evidence,
        links=links,
        sources=sources,
        verification_success_history=verification_success_history,
    )
    score = max(0.0, confidence["confidence"] * 100 - contradiction_history * 10)
    rating = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 50 else "D" if score >= 30 else "F"
    return {"score": round(score, 2), "rating": rating, "confidence": confidence}
