"""Calibrated knowledge confidence model."""

from __future__ import annotations

from typing import Any


def calibrated_confidence(
    *,
    coverage: float,
    trust: float,
    freshness: float,
    consistency: float,
    verification: float,
) -> dict[str, float]:
    components = {
        "coverage": _pct(coverage),
        "trust": _pct(trust),
        "freshness": _pct(freshness),
        "consistency": _pct(consistency),
        "verification": _pct(verification),
    }
    overall = (
        components["coverage"] * 0.20
        + components["trust"] * 0.25
        + components["freshness"] * 0.15
        + components["consistency"] * 0.20
        + components["verification"] * 0.20
    )
    return {**components, "overall": round(overall, 2)}


def confidence_from_assets(assets: dict[str, Any]) -> dict[str, float]:
    acquisition = assets.get("acquisition", {})
    verification = acquisition.get("verification", {})
    confidence = acquisition.get("confidence", {}).get("confidence", 0)
    quality = acquisition.get("quality", {}).get("score", 0) / 100.0
    unsupported = len(verification.get("unsupported", []))
    claims = len(verification.get("claims", []))
    coverage = len(acquisition.get("links", [])) / max(1, claims)
    source_types = {item.get("source_type") for item in acquisition.get("candidate_evidence", [])}
    source_refs = [item.get("source_reference") for item in acquisition.get("candidate_evidence", [])]
    evidence_count = len(acquisition.get("candidate_evidence", []))
    diversity = min(1.0, len(source_types) / max(1, min(5, evidence_count)))
    unique_ref_ratio = len(set(source_refs)) / max(1, len(source_refs))
    trust = confidence * (0.55 + diversity * 0.25 + unique_ref_ratio * 0.20)
    consistency = 1.0 - min(1.0, len(verification.get("contradicted", [])) / max(1, claims))
    verification_rate = 1.0 - min(1.0, unsupported / max(1, claims))
    return calibrated_confidence(
        coverage=min(1.0, coverage),
        trust=trust,
        freshness=quality,
        consistency=consistency,
        verification=verification_rate,
    )


def _pct(value: float) -> float:
    return round(max(0.0, min(1.0, value)) * 100, 2)
