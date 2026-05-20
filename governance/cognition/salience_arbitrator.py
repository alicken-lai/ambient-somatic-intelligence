"""Salience arbitration across domains — fair bounded blending."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.cognition.sovereignty_limits import SovereigntyLimitsChecker
from observability.v04.metric_normalizer import clamp01


@dataclass
class SalienceClaim:
    domain: str
    salience: float
    confidence: float = 0.75
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "salience": round(self.salience, 4),
            "confidence": round(self.confidence, 4),
            "weight": round(self.weight, 4),
        }


@dataclass
class SalienceArbitrationResult:
    arbitrated_salience: float
    domain_weights: dict[str, float]
    fairness_score: float
    sovereignty_ok: bool
    claims: list[SalienceClaim] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "arbitrated_salience": round(self.arbitrated_salience, 4),
            "domain_weights": {k: round(v, 4) for k, v in self.domain_weights.items()},
            "fairness_score": round(self.fairness_score, 4),
            "sovereignty_ok": self.sovereignty_ok,
            "claims": [c.to_dict() for c in self.claims],
        }


class SalienceArbitrator:
    """Weighted fair arbitration — confidence-discounted, sovereignty-checked."""

    def __init__(self) -> None:
        self.sovereignty = SovereigntyLimitsChecker()

    def arbitrate(self, claims: list[SalienceClaim]) -> SalienceArbitrationResult:
        if not claims:
            return SalienceArbitrationResult(
                arbitrated_salience=0.0,
                domain_weights={},
                fairness_score=1.0,
                sovereignty_ok=True,
            )
        weighted: dict[str, float] = {}
        for c in claims:
            contrib = clamp01(c.salience) * clamp01(c.confidence) * c.weight
            weighted[c.domain] = weighted.get(c.domain, 0.0) + contrib
        sov = self.sovereignty.check_domain_shares(weighted)
        total_w = sum(weighted.values()) or 1.0
        domain_weights = {k: v / total_w for k, v in weighted.items()}
        arbitrated = sum(
            clamp01(c.salience) * clamp01(c.confidence) * domain_weights.get(c.domain, 0.0)
            for c in claims
        )
        n = len(claims)
        fairness = clamp01(1.0 - abs(max(domain_weights.values(), default=0) - 1.0 / max(n, 1)))
        if not sov.compliant:
            arbitrated *= 0.85
            fairness *= 0.9
        return SalienceArbitrationResult(
            arbitrated_salience=clamp01(arbitrated),
            domain_weights=domain_weights,
            fairness_score=fairness,
            sovereignty_ok=sov.compliant,
            claims=list(claims),
        )
