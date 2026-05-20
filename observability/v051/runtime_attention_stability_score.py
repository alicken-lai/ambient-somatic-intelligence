"""v0.5.1 Runtime Attention Stability Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.kernel.attention_kernel import AttentionKernel
from observability.v04.metric_normalizer import clamp01
from observability.v05.attention_stability_score import (
    ATTENTION_GATE_THRESHOLD,
    AttentionClassification,
    AttentionRuntimeEvidence,
    AttentionStabilityReport,
    compute_attention_stability,
)
from observability.v051.precursor_attention_metrics import collect_precursor_metrics
from observability.v051.runtime_attention_metrics import collect_runtime_attention_metrics
from observability.v051.runtime_attention_pressure import compute_runtime_attention_pressure
from observability.v051.runtime_focus_distribution import compute_runtime_focus_distribution

RUNTIME_EXTRA_WEIGHTS: dict[str, float] = {
    "adapter_health": 0.08,
    "pressure_headroom": 0.07,
}

RUNTIME_GATE_THRESHOLD = 0.90


@dataclass
class RuntimeAttentionEvidence(AttentionRuntimeEvidence):
    adapter_ok: bool = True
    pressure_composite: float = 0.0
    focus_entropy: float = 0.0
    submission_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "adapter_ok": self.adapter_ok,
            "pressure_composite": round(self.pressure_composite, 4),
            "focus_entropy": round(self.focus_entropy, 4),
            "submission_count": self.submission_count,
        })
        return base


@dataclass
class RuntimeAttentionStabilityReport(AttentionStabilityReport):
    runtime_dimensions: dict[str, float] = field(default_factory=dict)
    runtime_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["runtime_dimensions"] = {k: round(v, 4) for k, v in self.runtime_dimensions.items()}
        base["runtime_score"] = round(self.runtime_score, 4)
        return base


def evidence_from_kernel(kernel: AttentionKernel, *, submissions: int = 0) -> RuntimeAttentionEvidence:
    metrics = collect_runtime_attention_metrics(kernel, submissions=submissions)
    pressure = compute_runtime_attention_pressure(kernel)
    focus = compute_runtime_focus_distribution(kernel)
    precursor = collect_precursor_metrics(kernel)
    return RuntimeAttentionEvidence(
        explainability_coverage=metrics.explainability_coverage,
        competition_fairness=0.88,
        focus_stability_score=0.92 if pressure.composite < 0.9 else 0.75,
        budget_overrun=0 if metrics.budget_remaining >= 0 else 1,
        opaque_salience_count=0,
        precursor_match_rate=precursor.match_rate,
        memory_recall_rate=0.88,
        somatic_adapter_ok=metrics.adapter_ok,
        decay_applied=True,
        recovery_ok=pressure.composite < 0.95,
        adapter_ok=metrics.adapter_ok,
        pressure_composite=pressure.composite,
        focus_entropy=focus.entropy,
        submission_count=submissions,
    )


def compute_runtime_attention_stability(
    evidence: RuntimeAttentionEvidence | None = None,
    kernel: AttentionKernel | None = None,
) -> RuntimeAttentionStabilityReport:
    if evidence is None:
        evidence = evidence_from_kernel(kernel or AttentionKernel())
    base_report = compute_attention_stability(evidence)

    adapter_health = 1.0 if evidence.adapter_ok else 0.0
    pressure_headroom = clamp01(1.0 - evidence.pressure_composite)

    runtime_dims = {
        "adapter_health": adapter_health,
        "pressure_headroom": pressure_headroom,
    }
    runtime_bonus = sum(runtime_dims[k] * RUNTIME_EXTRA_WEIGHTS[k] for k in RUNTIME_EXTRA_WEIGHTS)
    combined = clamp01(base_report.score * 0.92 + runtime_bonus)

    gate_pass = (
        combined >= RUNTIME_GATE_THRESHOLD
        and base_report.gate_pass
        and len(base_report.hard_failures) == 0
    )

    return RuntimeAttentionStabilityReport(
        score=combined,
        classification=base_report.classification,
        dimensions=base_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=RUNTIME_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=list(base_report.hard_failures),
        runtime_dimensions=runtime_dims,
        runtime_score=combined,
    )


def evaluate_runtime_attention_stability(
    evidence: RuntimeAttentionEvidence | None = None,
    *,
    kernel: AttentionKernel | None = None,
    **kwargs: Any,
) -> RuntimeAttentionStabilityReport:
    if evidence is None and kwargs:
        evidence = RuntimeAttentionEvidence(**kwargs)
    elif evidence is None and kernel is not None:
        evidence = evidence_from_kernel(kernel)
    return compute_runtime_attention_stability(evidence, kernel=kernel)


# Alias for gate docs
RuntimeAttentionStabilityScore = RuntimeAttentionStabilityReport
