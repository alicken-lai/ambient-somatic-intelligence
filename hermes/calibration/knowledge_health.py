"""Knowledge health scoring."""

from __future__ import annotations

from hermes.calibration.confidence_model import calibrated_confidence


def compute_knowledge_health(
    *,
    trust: float,
    freshness: float,
    consistency: float,
    verification: float,
    drift: float,
    inflation: float,
    coverage: float = 1.0,
) -> dict[str, object]:
    confidence = calibrated_confidence(
        coverage=coverage,
        trust=trust,
        freshness=freshness,
        consistency=consistency,
        verification=verification,
    )
    health = confidence["overall"] - (drift * 20) - (inflation * 20)
    health = round(max(0.0, min(100.0, health)), 2)
    risk = "low" if health >= 75 else "medium" if health >= 50 else "high"
    return {"health_score": health, "risk_level": risk, "confidence": confidence}
