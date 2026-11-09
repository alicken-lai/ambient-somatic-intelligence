"""Evidence confidence model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hermes.acquisition.evidence_linker import EvidenceLink
from hermes.acquisition.sources import EvidenceSource
from hermes.verification.evidence import Evidence


def calculate_confidence(
    *,
    evidence: list[Evidence],
    links: list[EvidenceLink],
    sources: dict[str, EvidenceSource],
    verification_success_history: float = 0.0,
) -> dict[str, Any]:
    support_count = len(links)
    source_types = {item.source_type for item in evidence}
    source_diversity = len(source_types)
    avg_trust = _avg([_trust_for(item, sources) for item in evidence])
    freshness = _freshness(evidence)
    confidence = min(
        1.0,
        support_count * 0.18
        + min(source_diversity, 4) * 0.12
        + avg_trust * 0.3
        + freshness * 0.2
        + verification_success_history * 0.1,
    )
    reasoning = [
        f"support_count={support_count}",
        f"source_diversity={source_diversity}",
        f"avg_source_trust={avg_trust:.2f}",
        f"freshness={freshness:.2f}",
        f"verification_success_history={verification_success_history:.2f}",
    ]
    return {"confidence": round(confidence, 4), "reasoning": reasoning}


def _trust_for(evidence: Evidence, sources: dict[str, EvidenceSource]) -> float:
    for source in sources.values():
        if source.source_type == evidence.source_type:
            return source.trust_level
    return 0.5


def _freshness(evidence: list[Evidence]) -> float:
    if not evidence:
        return 0.0
    now = datetime.now(timezone.utc)
    values = []
    for item in evidence:
        try:
            ts = datetime.fromisoformat(item.timestamp)
        except ValueError:
            values.append(0.5)
            continue
        values.append(max(0.0, 1.0 - min((now - ts).days, 365) / 365))
    return _avg(values)


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
