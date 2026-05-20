"""v0.6.0 Cognitive Governance Stability Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.governed_attention_activation import GovernedAttentionActivation
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from governance.cognition.salience_arbitrator import SalienceClaim
from observability.v04.metric_normalizer import clamp01
from observability.v054.calibration_stability_score import (
    CalibrationAttentionEvidence,
    CalibrationStabilityReport,
    evaluate_calibration_stability,
    evidence_from_calibrated_forecaster,
)
from observability.v060.arbitration_metrics import collect_arbitration_metrics
from observability.v060.authority_metrics import collect_authority_metrics
from observability.v060.replay_authority_metrics import collect_replay_authority_metrics
from observability.v060.sovereignty_metrics import collect_sovereignty_metrics
from observability.v060.uncertainty_override_metrics import collect_uncertainty_override_metrics

COGNITIVE_GOVERNANCE_GATE_THRESHOLD = 0.90

GOVERNANCE_EXTRA_WEIGHTS: dict[str, float] = {
    "arbitration_fairness": 0.04,
    "sovereignty_compliance": 0.04,
    "uncertainty_discipline": 0.04,
    "replay_bounded": 0.03,
}


@dataclass
class CognitiveGovernanceAttentionEvidence(CalibrationAttentionEvidence):
    arbitration_fairness: float = 0.88
    sovereignty_compliance_rate: float = 1.0
    uncertainty_override_rate: float = 0.15
    replay_bounded_rate: float = 1.0
    governance_loop_detected: bool = False
    autonomous_execution_blocked: bool = True

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "arbitration_fairness": round(self.arbitration_fairness, 4),
            "sovereignty_compliance_rate": round(self.sovereignty_compliance_rate, 4),
            "uncertainty_override_rate": round(self.uncertainty_override_rate, 4),
            "replay_bounded_rate": round(self.replay_bounded_rate, 4),
            "governance_loop_detected": self.governance_loop_detected,
            "autonomous_execution_blocked": self.autonomous_execution_blocked,
        })
        return base


@dataclass
class CognitiveGovernanceStabilityReport(CalibrationStabilityReport):
    governance_dimensions: dict[str, float] = field(default_factory=dict)
    governance_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["governance_dimensions"] = {
            k: round(v, 4) for k, v in self.governance_dimensions.items()
        }
        base["governance_score"] = round(self.governance_score, 4)
        return base


def evidence_from_governed_forecaster(
    forecaster: AttentionForecast,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    target_id: str = "governance-gate-target",
    submissions: int = 0,
) -> CognitiveGovernanceAttentionEvidence:
    br = bridge or RuntimeAttentionMemoryBridge(
        kernel=forecaster.kernel,
        store=forecaster.store,
    )
    base = evidence_from_calibrated_forecaster(
        forecaster, bridge=br, target_id=target_id, submissions=submissions
    )
    claims = [
        SalienceClaim("telemetry", 0.55, 0.8),
        SalienceClaim("somatic", 0.45, 0.75),
        SalienceClaim("governance", 0.25, 0.9),
    ]
    arb_met = collect_arbitration_metrics(claims, uncertainty=0.35)
    sov_met = collect_sovereignty_metrics([
        {"telemetry": 0.35, "somatic": 0.3, "governance": 0.2, "memory": 0.15},
    ])
    unc_met = collect_uncertainty_override_metrics([(0.6, 0.4), (0.7, 0.75)])
    rep_met = collect_replay_authority_metrics([(0.6, 0.2), (0.5, 0.1)])
    auth_met = collect_authority_metrics([
        {"base_salience": 0.5, "domain": "telemetry"},
        {"base_salience": 0.55, "domain": "somatic", "somatic_strength": 0.6},
    ])

    return CognitiveGovernanceAttentionEvidence(
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
        mean_calibrated_confidence=base.mean_calibrated_confidence,
        fp_rate=base.fp_rate,
        humility_factor_mean=base.humility_factor_mean,
        cap_violations=base.cap_violations,
        certainty_never_reached=base.certainty_never_reached,
        arbitration_fairness=arb_met.mean_fairness,
        sovereignty_compliance_rate=sov_met.compliance_rate,
        uncertainty_override_rate=unc_met.override_rate,
        replay_bounded_rate=rep_met.bounded_rate,
        governance_loop_detected=sov_met.recursive_blocks > 0,
        autonomous_execution_blocked=auth_met.somatic_bounded_rate >= 0.99,
    )


def compute_cognitive_governance_stability(
    evidence: CognitiveGovernanceAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
) -> CognitiveGovernanceStabilityReport:
    if evidence is None:
        fc = forecaster or AttentionForecast(kernel=kernel)
        evidence = evidence_from_governed_forecaster(fc, bridge=bridge)

    cal_report = evaluate_calibration_stability(evidence, forecaster=forecaster, bridge=bridge)

    arbitration_fairness = clamp01(evidence.arbitration_fairness)
    sovereignty_compliance = clamp01(evidence.sovereignty_compliance_rate)
    uncertainty_discipline = clamp01(1.0 - evidence.uncertainty_override_rate * 0.5)
    replay_bounded = clamp01(evidence.replay_bounded_rate)

    gov_dims = {
        "arbitration_fairness": arbitration_fairness,
        "sovereignty_compliance": sovereignty_compliance,
        "uncertainty_discipline": uncertainty_discipline,
        "replay_bounded": replay_bounded,
    }
    gov_bonus = sum(gov_dims[k] * GOVERNANCE_EXTRA_WEIGHTS[k] for k in GOVERNANCE_EXTRA_WEIGHTS)
    combined = clamp01(cal_report.calibration_score * 0.83 + gov_bonus)

    hard_failures = list(cal_report.hard_failures)
    if evidence.governance_loop_detected:
        hard_failures.append("governance_loop_detected")
    if not evidence.autonomous_execution_blocked:
        hard_failures.append("autonomous_execution_not_blocked")
    if evidence.sovereignty_compliance_rate < 0.5:
        hard_failures.append("sovereignty_compliance_low")
    if evidence.arbitration_fairness < 0.5:
        hard_failures.append("arbitration_unfair")

    gate_pass = (
        combined >= COGNITIVE_GOVERNANCE_GATE_THRESHOLD
        and cal_report.gate_pass
        and len(hard_failures) == 0
    )

    return CognitiveGovernanceStabilityReport(
        score=combined,
        classification=cal_report.classification,
        dimensions=cal_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=COGNITIVE_GOVERNANCE_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=hard_failures,
        runtime_dimensions=cal_report.runtime_dimensions,
        runtime_score=cal_report.runtime_score,
        memory_dimensions=cal_report.memory_dimensions,
        memory_score=cal_report.memory_score,
        forecast_dimensions=cal_report.forecast_dimensions,
        forecast_score=cal_report.forecast_score,
        calibration_dimensions=cal_report.calibration_dimensions,
        calibration_score=cal_report.calibration_score,
        governance_dimensions=gov_dims,
        governance_score=combined,
    )


def evaluate_cognitive_governance_stability(
    evidence: CognitiveGovernanceAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
    **kwargs: Any,
) -> CognitiveGovernanceStabilityReport:
    if evidence is None and kwargs:
        evidence = CognitiveGovernanceAttentionEvidence(**kwargs)
    return compute_cognitive_governance_stability(
        evidence, forecaster=forecaster, bridge=bridge, kernel=kernel
    )


CognitiveGovernanceStabilityScore = CognitiveGovernanceStabilityReport
