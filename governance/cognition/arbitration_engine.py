"""Arbitration engine — coordinates salience, somatic, replay, uncertainty paths."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.cognition.replay_authority import ReplayAuthority
from governance.cognition.salience_arbitrator import SalienceArbitrator, SalienceClaim
from governance.cognition.somatic_authority import SomaticAuthority
from governance.cognition.sovereignty_limits import SovereigntyLimitsChecker
from governance.cognition.uncertainty_override import UncertaintyOverride
from observability.v04.metric_normalizer import clamp01


@dataclass
class ArbitrationResult:
    final_salience: float
    arbitration_fairness: float
    sovereignty_compliant: bool
    uncertainty_applied: bool
    replay_bounded: bool
    somatic_bounded: bool
    governance_depth: int
    trace: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "final_salience": round(self.final_salience, 4),
            "arbitration_fairness": round(self.arbitration_fairness, 4),
            "sovereignty_compliant": self.sovereignty_compliant,
            "uncertainty_applied": self.uncertainty_applied,
            "replay_bounded": self.replay_bounded,
            "somatic_bounded": self.somatic_bounded,
            "governance_depth": self.governance_depth,
            "trace": list(self.trace),
        }


class ArbitrationEngine:
    """Single-pass arbitration — no recursive governance loops."""

    def __init__(self, *, governance_depth: int = 1) -> None:
        self.arbitrator = SalienceArbitrator()
        self.somatic = SomaticAuthority()
        self.replay = ReplayAuthority()
        self.uncertainty = UncertaintyOverride()
        self.sovereignty = SovereigntyLimitsChecker()
        self._depth = governance_depth

    def arbitrate(
        self,
        claims: list[SalienceClaim],
        *,
        uncertainty: float = 0.3,
        replay_hint: float = 0.0,
        replay_confidence: float = 0.0,
    ) -> ArbitrationResult:
        trace: list[str] = []
        if not self.sovereignty.check_governance_depth(self._depth):
            return ArbitrationResult(
                final_salience=0.0,
                arbitration_fairness=0.0,
                sovereignty_compliant=False,
                uncertainty_applied=False,
                replay_bounded=True,
                somatic_bounded=True,
                governance_depth=self._depth,
                trace=["governance_depth_exceeded"],
            )
        trace.append("salience_arbitration")
        arb = self.arbitrator.arbitrate(claims)
        sal = arb.arbitrated_salience
        primary = claims[0] if claims else SalienceClaim(domain="telemetry", salience=sal)
        is_somatic = primary.domain == "somatic"
        trace.append("somatic_authority")
        som = self.somatic.apply(sal, somatic_strength=primary.confidence, is_somatic=is_somatic)
        sal = som.governed_salience
        if replay_hint > 0:
            trace.append("replay_blend")
            rep = self.replay.blend(sal, replay_hint, replay_confidence=replay_confidence)
            sal = rep.live_weight
            replay_bounded = rep.bounded
        else:
            replay_bounded = True
        trace.append("uncertainty_override")
        unc = self.uncertainty.apply(sal, uncertainty)
        sal = unc.governed_salience
        return ArbitrationResult(
            final_salience=clamp01(sal),
            arbitration_fairness=arb.fairness_score,
            sovereignty_compliant=arb.sovereignty_ok,
            uncertainty_applied=unc.override_applied,
            replay_bounded=replay_bounded,
            somatic_bounded=som.bounded,
            governance_depth=self._depth,
            trace=trace,
        )
