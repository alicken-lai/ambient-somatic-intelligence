"""Trust-weighted verification."""

from __future__ import annotations

from hermes.acquisition.sources import EvidenceSource
from hermes.verification.evidence import Evidence


def trust_weighted_verification(evidence: list[Evidence], sources: dict[str, EvidenceSource], *, historical_reliability: float = 0.0) -> dict[str, float]:
    if not evidence:
        return {"weighted_confidence": 0.0, "evidence_weight": 0.0}
    weights = []
    for item in evidence:
        trust = next((source.trust_level for source in sources.values() if source.source_type == item.source_type), 0.5)
        weights.append(item.confidence * trust)
    evidence_weight = sum(weights) / len(weights)
    weighted = min(1.0, evidence_weight * 0.85 + historical_reliability * 0.15)
    return {"weighted_confidence": round(weighted, 4), "evidence_weight": round(evidence_weight, 4)}
