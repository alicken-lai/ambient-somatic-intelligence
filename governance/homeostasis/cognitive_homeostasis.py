"""Cognitive homeostasis — observational stabilization after meta-reflection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.homeostasis.attention_stabilizer import AttentionStabilizer
from governance.homeostasis.calibration_recovery import CalibrationRecovery
from governance.homeostasis.coherence_recovery import CoherenceRecovery
from governance.homeostasis.reflection_balancer import ReflectionBalancer
from governance.homeostasis.salience_damping import SalienceDamping
from governance.homeostasis.stabilization_state import StabilizationState, StabilizationStateTracker
from governance.homeostasis.uncertainty_rebalancer import UncertaintyRebalancer
from observability.v04.metric_normalizer import clamp01


@dataclass
class HomeostasisVerdict:
    stable: bool
    homeostasis_score: float
    stabilization_pressure: float = 0.0
    advisory_damp_factor: float = 0.0
    stabilization_state: dict[str, Any] | None = None
    recommendations: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stable": self.stable,
            "homeostasis_score": round(self.homeostasis_score, 4),
            "stabilization_pressure": round(self.stabilization_pressure, 4),
            "advisory_damp_factor": round(self.advisory_damp_factor, 4),
            "stabilization_state": self.stabilization_state,
            "recommendations": list(self.recommendations),
            "trace": list(self.trace),
            "disclaimer": "homeostasis_advisory_not_autonomous_execution",
        }


class CognitiveHomeostasis:
    """
    Bounded homeostatic assessment after meta-cognitive reflection.

    Observational only — recommendations never override governance or Guardian.
    """

    HOMEOSTASIS_FLOOR = 0.58

    def __init__(self) -> None:
        self.attention_stabilizer = AttentionStabilizer()
        self.salience_damping = SalienceDamping()
        self.coherence_recovery = CoherenceRecovery()
        self.reflection_balancer = ReflectionBalancer()
        self.calibration_recovery = CalibrationRecovery()
        self.uncertainty_rebalancer = UncertaintyRebalancer()
        self.state_tracker = StabilizationStateTracker()
        self._evaluations = 0

    def evaluate_after_reflection(
        self,
        meta: Any,
        *,
        governed_salience: float,
        coherence_score: float,
        coherence_ok: bool = True,
        coherence_verdict: dict[str, Any] | None = None,
        uncertainty: float = 0.35,
        focus_entropy: float = 0.5,
        budget_overrun: bool = False,
        mean_calibrated_confidence: float = 0.7,
        fp_rate: float = 0.1,
        cap_violations: int = 0,
    ) -> HomeostasisVerdict:
        self._evaluations += 1

        att_p = self.attention_stabilizer.pressure(
            focus_entropy=focus_entropy,
            budget_overrun=budget_overrun,
            pathology_pressure=meta.pathology_pressure,
        )
        damp = self.salience_damping.advisory_damp_factor(
            governed_salience=governed_salience,
            pathology_pressure=meta.pathology_pressure,
        )
        coh_gap = self.coherence_recovery.gap(
            coherence_score=coherence_score, coherence_ok=coherence_ok
        )
        refl_load = self.reflection_balancer.load(
            introspection_pressure=meta.introspection_pressure,
            recursive_pressure=meta.recursive_pressure,
            boundary_pressure=meta.boundary_pressure,
            degradation_pressure=meta.degradation_pressure,
        )
        cal_gap = self.calibration_recovery.gap(
            mean_calibrated_confidence=mean_calibrated_confidence,
            fp_rate=fp_rate,
            cap_violations=cap_violations,
        )
        unc_skew = self.uncertainty_rebalancer.skew(
            uncertainty=uncertainty,
            governed_salience=governed_salience,
            metacognition_score=meta.quality_score,
        )

        state = StabilizationState(
            attention_pressure=att_p,
            salience_variance=self.salience_damping.oscillation_pressure(),
            coherence_gap=coh_gap,
            reflection_load=refl_load,
            calibration_gap=cal_gap,
            uncertainty_skew=unc_skew,
            trace=["homeostasis_evaluate"],
        )
        state = self.state_tracker.update(state)
        trend_p = self.state_tracker.trend_pressure()
        composite = clamp01(state.composite_pressure() + trend_p * 0.15)

        recs: list[str] = []
        recs.extend(
            self.attention_stabilizer.recommend(
                focus_entropy=focus_entropy,
                budget_overrun=budget_overrun,
                pathology_pressure=meta.pathology_pressure,
            )
        )
        recs.extend(
            self.salience_damping.recommend(
                governed_salience=governed_salience,
                pathology_pressure=meta.pathology_pressure,
            )
        )
        recs.extend(
            self.coherence_recovery.recommend(
                coherence_score=coherence_score, coherence_ok=coherence_ok
            )
        )
        recs.extend(
            self.reflection_balancer.recommend(
                introspection_pressure=meta.introspection_pressure,
                recursive_pressure=meta.recursive_pressure,
                boundary_pressure=meta.boundary_pressure,
                degradation_pressure=meta.degradation_pressure,
            )
        )
        recs.extend(
            self.calibration_recovery.recommend(
                calibration_pressure=meta.calibration_pressure,
                mean_calibrated_confidence=mean_calibrated_confidence,
                fp_rate=fp_rate,
                cap_violations=cap_violations,
            )
        )
        recs.extend(
            self.uncertainty_rebalancer.recommend(
                uncertainty=uncertainty,
                governed_salience=governed_salience,
                metacognition_score=meta.quality_score,
            )
        )

        base = clamp01(
            meta.quality_score * 0.45
            + coherence_score * 0.30
            + state.level * 0.25
        )
        adjusted = clamp01(base * (1.0 - composite * 0.30))
        stable = adjusted >= self.HOMEOSTASIS_FLOOR and len(recs) == 0

        return HomeostasisVerdict(
            stable=stable,
            homeostasis_score=adjusted,
            stabilization_pressure=composite,
            advisory_damp_factor=damp,
            stabilization_state=state.to_dict(),
            recommendations=recs,
            trace=[
                "homeostasis_post_reflection",
                f"score:{adjusted:.3f}",
                f"pressure:{composite:.3f}",
            ],
        )
