"""Echo chamber risk detection."""

from __future__ import annotations

from typing import Any


def detect_echo_chamber(*, confidence: float, trust: float, diversity_score: float, self_reference: float) -> dict[str, Any]:
    risk = 0.0
    reasons: list[str] = []
    if confidence >= 0.85:
        risk += 0.25
        reasons.append("high confidence")
    if trust >= 0.8:
        risk += 0.2
        reasons.append("high trust")
    if diversity_score < 50:
        risk += 0.3
        reasons.append("low source diversity")
    if self_reference >= 0.5:
        risk += 0.25
        reasons.append("high self-reference")
    return {
        "echo_risk": round(min(1.0, risk), 4),
        "reason": "; ".join(reasons) if reasons else "no echo chamber indicators",
    }
