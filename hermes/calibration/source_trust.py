"""Baseline and evolving source trust."""

from __future__ import annotations

from hermes.acquisition.sources import EvidenceSource
from hermes.calibration.trust import TrustRecord


DEFAULT_SOURCE_TRUST = {
    "Guardian Findings": 1.00,
    "Guardian Logs": 1.00,
    "Passed Tests": 0.95,
    "Tests": 0.95,
    "Verification Reports": 0.90,
    "Benchmarks": 0.85,
    "Failure Reports": 0.80,
    "Playbooks": 0.75,
    "Skills": 0.70,
    "Provider Outputs": 0.60,
    "Reports": 0.82,
    "DMN": 0.75,
    "Heuristics": 0.40,
}


def baseline_source_trust(source: EvidenceSource) -> TrustRecord:
    score = DEFAULT_SOURCE_TRUST.get(source.source_type, source.trust_level)
    return TrustRecord(
        trust_id=f"trust-source-{source.source_id}",
        entity_type="source",
        entity_id=source.source_id,
        trust_score=round(score, 4),
        reasoning=[f"baseline source type trust for {source.source_type}"],
    )


def evolve_source_trust(base_score: float, *, verification_success: int = 0, verification_failure: int = 0, contradictions: int = 0, freshness: float = 1.0) -> float:
    score = base_score + min(0.1, verification_success * 0.01)
    score -= verification_failure * 0.04
    score -= contradictions * 0.08
    score *= max(0.5, freshness)
    return round(max(0.0, min(1.0, score)), 4)
