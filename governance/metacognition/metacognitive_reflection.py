"""Metacognitive reflection — bounded meta-assessment after coherence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.metacognition.attention_pathology import AttentionPathology
from governance.metacognition.calibration_reflection import CalibrationReflection
from governance.metacognition.cognition_quality import CognitionQuality
from governance.metacognition.coherence_reflection import CoherenceReflection
from governance.metacognition.degradation_detector import DegradationDetector
from governance.metacognition.introspection_cap import IntrospectionCap
from governance.metacognition.recursive_reflection_guard import RecursiveReflectionGuard
from governance.metacognition.reflection_boundary import ReflectionBoundary
from observability.v04.metric_normalizer import clamp01


@dataclass
class MetacognitiveVerdict:
    reflective: bool
    quality_score: float
    degradation_pressure: float = 0.0
    pathology_pressure: float = 0.0
    coherence_reflection_pressure: float = 0.0
    calibration_pressure: float = 0.0
    boundary_pressure: float = 0.0
    introspection_pressure: float = 0.0
    recursive_pressure: float = 0.0
    reasons: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reflective": self.reflective,
            "quality_score": round(self.quality_score, 4),
            "degradation_pressure": round(self.degradation_pressure, 4),
            "pathology_pressure": round(self.pathology_pressure, 4),
            "coherence_reflection_pressure": round(
                self.coherence_reflection_pressure, 4
            ),
            "calibration_pressure": round(self.calibration_pressure, 4),
            "boundary_pressure": round(self.boundary_pressure, 4),
            "introspection_pressure": round(self.introspection_pressure, 4),
            "recursive_pressure": round(self.recursive_pressure, 4),
            "reasons": list(self.reasons),
            "trace": list(self.trace),
            "disclaimer": "metacognitive_advisory_not_consciousness_claim",
        }


class MetacognitiveReflection:
    """
    Bounded meta-cognitive reflection after coherence evaluation.

    Observational only — does not override governance or Guardian.
    """

    REFLECTION_FLOOR = 0.55

    def __init__(self) -> None:
        self.quality = CognitionQuality()
        self.degradation = DegradationDetector()
        self.pathology = AttentionPathology()
        self.coherence_reflection = CoherenceReflection()
        self.calibration_reflection = CalibrationReflection()
        self.boundary = ReflectionBoundary()
        self.introspection_cap = IntrospectionCap()
        self.recursive_guard = RecursiveReflectionGuard()
        self._homeostasis: Any = None
        self._evaluations = 0

    def _get_homeostasis(self) -> Any:
        if self._homeostasis is None:
            from governance.homeostasis.cognitive_homeostasis import CognitiveHomeostasis

            self._homeostasis = CognitiveHomeostasis()
        return self._homeostasis

    def evaluate_after_coherence(
        self,
        *,
        governed_salience: float,
        coherence_score: float,
        coherence_verdict: dict[str, Any] | None = None,
        constitutional_compliant: bool = True,
        identity_trusted: bool = True,
        accepted: bool = True,
        route_name: str = "attention_submit",
        metadata: dict[str, Any] | None = None,
        focus_entropy: float = 0.5,
        budget_overrun: bool = False,
        opaque_salience_count: int = 0,
        submission_count: int = 0,
        mean_calibrated_confidence: float = 0.7,
        fp_rate: float = 0.1,
        cap_violations: int = 0,
        certainty_never_reached: bool = True,
    ) -> MetacognitiveVerdict:
        self._evaluations += 1
        if self.recursive_guard.block_recursive_route(route_name):
            return MetacognitiveVerdict(
                reflective=False,
                quality_score=0.0,
                recursive_pressure=0.9,
                reasons=["recursive_reflection_blocked"],
                trace=["metacognitive_blocked_recursive"],
            )

        if not self.introspection_cap.enter():
            return MetacognitiveVerdict(
                reflective=False,
                quality_score=0.0,
                introspection_pressure=0.9,
                reasons=["introspection_cap_exceeded"],
                trace=["metacognitive_cap_blocked"],
            )

        try:
            boundary_p = self.boundary.pressure(
                route_name=route_name, metadata=metadata
            )
            recursive_p = self.recursive_guard.pressure(route_name)
            introspection_p = self.introspection_cap.pressure()

            quality_score = self.quality.score(
                governed_salience=governed_salience,
                coherence_score=coherence_score,
                constitutional_compliant=constitutional_compliant,
                identity_trusted=identity_trusted,
                accepted=accepted,
            )
            self.degradation.record_quality(quality_score)
            degradation_p = self.degradation.pressure()
            pathology_p = self.pathology.pressure(
                focus_entropy=focus_entropy,
                budget_overrun=budget_overrun,
                opaque_salience_count=opaque_salience_count,
                submission_count=submission_count,
            )
            coherence_refl_p = self.coherence_reflection.pressure(coherence_verdict)
            calibration_p = self.calibration_reflection.pressure(
                mean_calibrated_confidence=mean_calibrated_confidence,
                fp_rate=fp_rate,
                cap_violations=cap_violations,
                certainty_never_reached=certainty_never_reached,
            )

            composite_pressure = clamp01(
                degradation_p * 0.22
                + pathology_p * 0.22
                + coherence_refl_p * 0.18
                + calibration_p * 0.15
                + boundary_p * 0.13
                + introspection_p * 0.05
                + recursive_p * 0.05
            )
            adjusted = clamp01(quality_score * (1.0 - composite_pressure * 0.35))

            reasons: list[str] = []
            if degradation_p >= 0.35:
                reasons.append("cognition_degrading")
            if pathology_p >= 0.35:
                reasons.extend(
                    self.pathology.labels(
                        focus_entropy=focus_entropy,
                        budget_overrun=budget_overrun,
                        opaque_salience_count=opaque_salience_count,
                        submission_count=submission_count,
                    )
                )
            if boundary_p >= 0.35:
                reasons.append("reflection_boundary_violation")
            if recursive_p >= 0.5:
                reasons.append("recursive_reflection_risk")

            reflective = adjusted >= self.REFLECTION_FLOOR and len(reasons) == 0
            self.recursive_guard.record(route_name)

            return MetacognitiveVerdict(
                reflective=reflective,
                quality_score=adjusted,
                degradation_pressure=degradation_p,
                pathology_pressure=pathology_p,
                coherence_reflection_pressure=coherence_refl_p,
                calibration_pressure=calibration_p,
                boundary_pressure=boundary_p,
                introspection_pressure=introspection_p,
                recursive_pressure=recursive_p,
                reasons=reasons,
                trace=[
                    "metacognitive_evaluate",
                    f"quality:{adjusted:.3f}",
                    f"pressure:{composite_pressure:.3f}",
                ],
            )
        finally:
            self.introspection_cap.exit()

    def stabilize_after_reflection(
        self,
        meta: MetacognitiveVerdict,
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
    ) -> Any:
        """Observational stabilization recommendations — never overrides governance."""
        return self._get_homeostasis().evaluate_after_reflection(
            meta,
            governed_salience=governed_salience,
            coherence_score=coherence_score,
            coherence_ok=coherence_ok,
            coherence_verdict=coherence_verdict,
            uncertainty=uncertainty,
            focus_entropy=focus_entropy,
            budget_overrun=budget_overrun,
            mean_calibrated_confidence=mean_calibrated_confidence,
            fp_rate=fp_rate,
            cap_violations=cap_violations,
        )
