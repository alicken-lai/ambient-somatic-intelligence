"""v0.5.4 Calibration Stability Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.calibration.confidence_cap import ABSOLUTE_MAX_CONFIDENCE
from attention.calibration.forecast_confidence import ForecastConfidenceCalibrator
from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from observability.v04.metric_normalizer import clamp01
from observability.v053.forecast_stability_score import (
    FORECAST_GATE_THRESHOLD,
    ForecastAttentionEvidence,
    ForecastStabilityReport,
    evaluate_forecast_stability,
    evidence_from_forecaster,
)
from observability.v054.calibration_metrics import collect_calibration_metrics
from observability.v054.confidence_cap_metrics import collect_confidence_cap_metrics
from observability.v054.false_positive_metrics import collect_false_positive_metrics
from observability.v054.humility_metrics import collect_humility_metrics

CALIBRATION_GATE_THRESHOLD = 0.90

CALIBRATION_EXTRA_WEIGHTS: dict[str, float] = {
    "confidence_discipline": 0.05,
    "fp_calibration": 0.04,
    "humility_health": 0.04,
    "cap_enforcement": 0.04,
}


@dataclass
class CalibrationAttentionEvidence(ForecastAttentionEvidence):
    mean_calibrated_confidence: float = 0.85
    fp_rate: float = 0.0
    humility_factor_mean: float = 0.95
    cap_violations: int = 0
    certainty_never_reached: bool = True

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "mean_calibrated_confidence": round(self.mean_calibrated_confidence, 4),
            "fp_rate": round(self.fp_rate, 4),
            "humility_factor_mean": round(self.humility_factor_mean, 4),
            "cap_violations": self.cap_violations,
            "certainty_never_reached": self.certainty_never_reached,
        })
        return base


@dataclass
class CalibrationStabilityReport(ForecastStabilityReport):
    calibration_dimensions: dict[str, float] = field(default_factory=dict)
    calibration_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["calibration_dimensions"] = {
            k: round(v, 4) for k, v in self.calibration_dimensions.items()
        }
        base["calibration_score"] = round(self.calibration_score, 4)
        return base


def evidence_from_calibrated_forecaster(
    forecaster: AttentionForecast,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    target_id: str = "calibration-gate-target",
    submissions: int = 0,
) -> CalibrationAttentionEvidence:
    br = bridge or RuntimeAttentionMemoryBridge(
        kernel=forecaster.kernel,
        store=forecaster.store,
    )
    base = evidence_from_forecaster(
        forecaster, bridge=br, target_id=target_id, submissions=submissions
    )
    result = forecaster.forecast(target_id)
    raw_confs = [p.band.confidence for p in result.projections] or [0.75]
    calibrator = ForecastConfidenceCalibrator()
    cal_met = collect_calibration_metrics(raw_confs, domain="forecast")
    from attention.calibration.confidence_cap import ConfidenceCap
    from attention.calibration.false_positive_tracker import FalsePositiveTracker
    from attention.calibration.forecast_humility import ForecastHumility

    cap_met = collect_confidence_cap_metrics(ConfidenceCap(), raw_confs)
    fp_met = collect_false_positive_metrics(calibrator.fp_tracker)
    hum_met = collect_humility_metrics(ForecastHumility(), raw_confs)

    return CalibrationAttentionEvidence(
        explainability_coverage=base.explainability_coverage,
        competition_fairness=base.competition_fairness,
        focus_stability_score=base.focus_stability_score,
        budget_overrun=base.budget_overrun,
        opaque_salience_count=base.opaque_salience_count,
        precursor_match_rate=base.precursor_match_rate,
        memory_recall_rate=base.memory_recall_rate,
        somatic_adapter_ok=base.somatic_adapter_ok,
        decay_applied=base.decay_applied,
        recovery_ok=base.recovery_ok,
        adapter_ok=base.adapter_ok,
        pressure_composite=base.pressure_composite,
        focus_entropy=base.focus_entropy,
        submission_count=base.submission_count,
        store_fill_ratio=base.store_fill_ratio,
        trace_coverage=base.trace_coverage,
        precursor_match_rate_mem=base.precursor_match_rate_mem,
        background_stability=base.background_stability,
        reinforcement_bounded=base.reinforcement_bounded,
        memory_count=base.memory_count,
        mean_projection_confidence=base.mean_projection_confidence,
        mean_band_width=base.mean_band_width,
        precursor_forecast_rate=base.precursor_forecast_rate,
        forecast_pressure_headroom=base.forecast_pressure_headroom,
        trajectory_stable=base.trajectory_stable,
        no_recursive_amplification=base.no_recursive_amplification,
        mean_calibrated_confidence=cal_met.mean_calibrated_confidence,
        fp_rate=fp_met.global_fp_rate,
        humility_factor_mean=hum_met.mean_humility_factor,
        cap_violations=cap_met.violations,
        certainty_never_reached=cal_met.certainty_violations == 0,
    )


def compute_calibration_stability(
    evidence: CalibrationAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
) -> CalibrationStabilityReport:
    if evidence is None:
        fc = forecaster or AttentionForecast(kernel=kernel)
        evidence = evidence_from_calibrated_forecaster(fc, bridge=bridge)

    forecast_report = evaluate_forecast_stability(evidence, forecaster=forecaster, bridge=bridge)

    confidence_discipline = clamp01(evidence.mean_calibrated_confidence)
    fp_calibration = clamp01(1.0 - evidence.fp_rate * 2.0)
    humility_health = clamp01(evidence.humility_factor_mean)
    cap_enforcement = clamp01(1.0 if evidence.cap_violations == 0 else 0.5)

    cal_dims = {
        "confidence_discipline": confidence_discipline,
        "fp_calibration": fp_calibration,
        "humility_health": humility_health,
        "cap_enforcement": cap_enforcement,
    }
    cal_bonus = sum(cal_dims[k] * CALIBRATION_EXTRA_WEIGHTS[k] for k in CALIBRATION_EXTRA_WEIGHTS)
    combined = clamp01(forecast_report.forecast_score * 0.84 + cal_bonus)

    hard_failures = list(forecast_report.hard_failures)
    if evidence.cap_violations > 0:
        hard_failures.append("confidence_cap_violation")
    if not evidence.certainty_never_reached:
        hard_failures.append("certainty_reached_forbidden")
    if evidence.mean_calibrated_confidence >= 1.0:
        hard_failures.append("uncapped_calibrated_confidence")

    gate_pass = (
        combined >= CALIBRATION_GATE_THRESHOLD
        and forecast_report.gate_pass
        and len(hard_failures) == 0
        and evidence.mean_calibrated_confidence <= ABSOLUTE_MAX_CONFIDENCE
    )

    return CalibrationStabilityReport(
        score=combined,
        classification=forecast_report.classification,
        dimensions=forecast_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=CALIBRATION_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=hard_failures,
        runtime_dimensions=forecast_report.runtime_dimensions,
        runtime_score=forecast_report.runtime_score,
        memory_dimensions=forecast_report.memory_dimensions,
        memory_score=forecast_report.memory_score,
        forecast_dimensions=forecast_report.forecast_dimensions,
        forecast_score=forecast_report.forecast_score,
        calibration_dimensions=cal_dims,
        calibration_score=combined,
    )


def evaluate_calibration_stability(
    evidence: CalibrationAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
    **kwargs: Any,
) -> CalibrationStabilityReport:
    if evidence is None and kwargs:
        evidence = CalibrationAttentionEvidence(**kwargs)
    return compute_calibration_stability(
        evidence, forecaster=forecaster, bridge=bridge, kernel=kernel
    )


CalibrationStabilityScore = CalibrationStabilityReport
