"""v0.5.3 Forecast Stability Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.forecasting.attention_forecast import AttentionForecast
from attention.forecasting.forecast_uncertainty import ForecastUncertainty
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from observability.v04.metric_normalizer import clamp01
from observability.v052.attention_memory_stability_score import (
    AttentionMemoryEvidence,
    AttentionMemoryStabilityReport,
    MEMORY_GATE_THRESHOLD,
    evaluate_attention_memory_stability,
    evidence_from_bridge,
)
from observability.v053.forecast_metrics import collect_forecast_metrics
from observability.v053.forecast_pressure import collect_forecast_pressure_metrics
from observability.v053.precursor_forecast_metrics import collect_precursor_forecast_metrics
from observability.v053.salience_projection_metrics import collect_salience_projection_metrics

FORECAST_GATE_THRESHOLD = 0.90

FORECAST_EXTRA_WEIGHTS: dict[str, float] = {
    "projection_discipline": 0.05,
    "uncertainty_calibration": 0.05,
    "precursor_forecast_health": 0.04,
    "pressure_headroom_forecast": 0.04,
}


@dataclass
class ForecastAttentionEvidence(AttentionMemoryEvidence):
    mean_projection_confidence: float = 0.85
    mean_band_width: float = 0.15
    precursor_forecast_rate: float = 0.0
    forecast_pressure_headroom: float = 0.9
    trajectory_stable: bool = True
    no_recursive_amplification: bool = True

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "mean_projection_confidence": round(self.mean_projection_confidence, 4),
            "mean_band_width": round(self.mean_band_width, 4),
            "precursor_forecast_rate": round(self.precursor_forecast_rate, 4),
            "forecast_pressure_headroom": round(self.forecast_pressure_headroom, 4),
            "trajectory_stable": self.trajectory_stable,
            "no_recursive_amplification": self.no_recursive_amplification,
        })
        return base


@dataclass
class ForecastStabilityReport(AttentionMemoryStabilityReport):
    forecast_dimensions: dict[str, float] = field(default_factory=dict)
    forecast_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["forecast_dimensions"] = {k: round(v, 4) for k, v in self.forecast_dimensions.items()}
        base["forecast_score"] = round(self.forecast_score, 4)
        return base


def evidence_from_forecaster(
    forecaster: AttentionForecast,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    target_id: str = "forecast-gate-target",
    submissions: int = 0,
) -> ForecastAttentionEvidence:
    br = bridge or RuntimeAttentionMemoryBridge(
        kernel=forecaster.kernel,
        store=forecaster.store,
    )
    base = evidence_from_bridge(br, kernel=forecaster.kernel, submissions=submissions)

    result = forecaster.forecast(target_id)
    fmet = collect_forecast_metrics(result)
    proj_met = collect_salience_projection_metrics(forecaster.projection, target_id)
    from attention.core.precursor_signal import PrecursorSignal

    prec_met = collect_precursor_forecast_metrics(
        forecaster.precursor_forecast,
        [PrecursorSignal(pattern_id="gate-pat", strength=0.6, domain="telemetry")],
    )
    press_met = collect_forecast_pressure_metrics(forecaster.pressure_forecast, target_id)

    return ForecastAttentionEvidence(
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
        mean_projection_confidence=fmet.mean_confidence,
        mean_band_width=proj_met.mean_band_width,
        precursor_forecast_rate=prec_met.mean_likelihood,
        forecast_pressure_headroom=press_met.headroom,
        trajectory_stable=fmet.trajectory_direction in ("stable", "rising"),
        no_recursive_amplification=True,
    )


def compute_forecast_stability(
    evidence: ForecastAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
) -> ForecastStabilityReport:
    if evidence is None:
        fc = forecaster or AttentionForecast(kernel=kernel)
        evidence = evidence_from_forecaster(fc, bridge=bridge)

    memory_report = evaluate_attention_memory_stability(evidence)

    projection_discipline = clamp01(evidence.mean_projection_confidence)
    uncertainty_cal = clamp01(1.0 - evidence.mean_band_width * 2.0)
    precursor_health = clamp01(0.75 + evidence.precursor_forecast_rate * 0.25)
    pressure_headroom_fc = clamp01(evidence.forecast_pressure_headroom)

    forecast_dims = {
        "projection_discipline": projection_discipline,
        "uncertainty_calibration": uncertainty_cal,
        "precursor_forecast_health": precursor_health,
        "pressure_headroom_forecast": pressure_headroom_fc,
    }
    forecast_bonus = sum(forecast_dims[k] * FORECAST_EXTRA_WEIGHTS[k] for k in FORECAST_EXTRA_WEIGHTS)
    combined = clamp01(memory_report.memory_score * 0.86 + forecast_bonus)

    hard_failures = list(memory_report.hard_failures)
    if not evidence.no_recursive_amplification:
        hard_failures.append("recursive_forecast_amplification")
    if evidence.mean_band_width > ForecastUncertainty().max_spread:
        hard_failures.append("uncertainty_band_exceeded")

    gate_pass = (
        combined >= FORECAST_GATE_THRESHOLD
        and memory_report.gate_pass
        and len(hard_failures) == 0
    )

    return ForecastStabilityReport(
        score=combined,
        classification=memory_report.classification,
        dimensions=memory_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=FORECAST_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=hard_failures,
        runtime_dimensions=memory_report.runtime_dimensions,
        runtime_score=memory_report.runtime_score,
        memory_dimensions=memory_report.memory_dimensions,
        memory_score=memory_report.memory_score,
        forecast_dimensions=forecast_dims,
        forecast_score=combined,
    )


def evaluate_forecast_stability(
    evidence: ForecastAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
    **kwargs: Any,
) -> ForecastStabilityReport:
    if evidence is None and kwargs:
        evidence = ForecastAttentionEvidence(**kwargs)
    return compute_forecast_stability(evidence, forecaster=forecaster, bridge=bridge, kernel=kernel)


ForecastStabilityScore = ForecastStabilityReport
