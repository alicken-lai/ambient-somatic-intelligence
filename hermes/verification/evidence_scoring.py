"""Evidence quality scoring."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hermes.verification.evidence import Evidence


def evidence_metrics(claims: list[Any], evidence: list[Evidence], statuses: dict[str, str], contradictions: list[dict[str, Any]]) -> dict[str, float]:
    total = len(claims)
    supported = sum(1 for claim in claims if statuses.get(_claim_id(claim)) == "verified")
    verified_or_checked = sum(1 for claim in claims if statuses.get(_claim_id(claim)) in {"verified", "unsupported", "contradicted"})
    unsupported = sum(1 for claim in claims if statuses.get(_claim_id(claim)) == "unsupported")
    contradiction_count = sum(1 for item in contradictions if item.get("contradiction"))
    freshness = _freshness(evidence)
    return {
        "claim_support_coverage": supported / total if total else 0.0,
        "verification_coverage": verified_or_checked / total if total else 0.0,
        "contradiction_rate": contradiction_count / total if total else 0.0,
        "unsupported_claim_rate": unsupported / total if total else 0.0,
        "evidence_freshness": freshness,
    }


def evidence_score(claims: list[Any], evidence: list[Evidence], statuses: dict[str, str], contradictions: list[dict[str, Any]]) -> float:
    metrics = evidence_metrics(claims, evidence, statuses, contradictions)
    score = (
        metrics["claim_support_coverage"] * 35
        + metrics["verification_coverage"] * 30
        + metrics["evidence_freshness"] * 15
        + (1 - metrics["unsupported_claim_rate"]) * 10
        + (1 - metrics["contradiction_rate"]) * 10
    )
    return round(max(0.0, min(100.0, score)), 2)


def _freshness(evidence: list[Evidence]) -> float:
    if not evidence:
        return 0.0
    now = datetime.now(timezone.utc)
    scores = []
    for item in evidence:
        try:
            ts = datetime.fromisoformat(item.timestamp)
        except ValueError:
            scores.append(0.5)
            continue
        age_days = max(0, (now - ts).days)
        scores.append(max(0.0, 1.0 - min(age_days, 365) / 365))
    return sum(scores) / len(scores)


def _claim_id(claim: Any) -> str:
    if isinstance(claim, dict):
        return str(claim.get("claim_id", ""))
    return str(claim.claim_id)
