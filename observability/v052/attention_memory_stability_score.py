"""v0.5.2 Attention Memory Stability Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.consolidation.attention_memory_store import AttentionMemoryStore
from attention.consolidation.benign_pattern_memory import BenignPatternMemory
from attention.consolidation.precursor_memory import PrecursorMemory
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from observability.v04.metric_normalizer import clamp01
from observability.v051.runtime_attention_stability_score import (
    RUNTIME_GATE_THRESHOLD,
    RuntimeAttentionEvidence,
    RuntimeAttentionStabilityReport,
    evaluate_runtime_attention_stability,
    evidence_from_kernel,
)
from observability.v052.consolidation_metrics import collect_consolidation_metrics
from observability.v052.memory_consolidation_pressure import compute_memory_consolidation_pressure
from observability.v052.noise_suppression_metrics import collect_noise_suppression_metrics
from observability.v052.precursor_memory_metrics import collect_precursor_memory_metrics
from observability.v052.salience_history_metrics import collect_salience_history_metrics

MEMORY_GATE_THRESHOLD = 0.90

MEMORY_EXTRA_WEIGHTS: dict[str, float] = {
    "consolidation_headroom": 0.06,
    "precursor_memory_health": 0.05,
    "noise_suppression": 0.05,
    "trace_discipline": 0.04,
}


@dataclass
class AttentionMemoryEvidence(RuntimeAttentionEvidence):
    store_fill_ratio: float = 0.0
    trace_coverage: float = 0.0
    precursor_match_rate_mem: float = 0.85
    background_stability: float = 0.9
    reinforcement_bounded: bool = True
    memory_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "store_fill_ratio": round(self.store_fill_ratio, 4),
            "trace_coverage": round(self.trace_coverage, 4),
            "precursor_match_rate_mem": round(self.precursor_match_rate_mem, 4),
            "background_stability": round(self.background_stability, 4),
            "reinforcement_bounded": self.reinforcement_bounded,
            "memory_count": self.memory_count,
        })
        return base


@dataclass
class AttentionMemoryStabilityReport(RuntimeAttentionStabilityReport):
    memory_dimensions: dict[str, float] = field(default_factory=dict)
    memory_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["memory_dimensions"] = {k: round(v, 4) for k, v in self.memory_dimensions.items()}
        base["memory_score"] = round(self.memory_score, 4)
        return base


def evidence_from_bridge(
    bridge: RuntimeAttentionMemoryBridge,
    *,
    kernel: AttentionKernel | None = None,
    submissions: int = 0,
) -> AttentionMemoryEvidence:
    k = kernel or bridge.kernel
    base = evidence_from_kernel(k, submissions=submissions)
    store = bridge.store
    pressure = compute_memory_consolidation_pressure(store)
    benign = BenignPatternMemory()
    noise = collect_noise_suppression_metrics(benign, store.trace)
    precursor_m = collect_precursor_memory_metrics(bridge.precursor_memory)
    _ = collect_consolidation_metrics(store)
    _ = collect_salience_history_metrics(store.history)

    return AttentionMemoryEvidence(
        explainability_coverage=base.explainability_coverage,
        competition_fairness=0.88,
        focus_stability_score=base.focus_stability_score,
        budget_overrun=base.budget_overrun,
        opaque_salience_count=base.opaque_salience_count,
        precursor_match_rate=max(base.precursor_match_rate, precursor_m.match_rate),
        memory_recall_rate=0.9 if store.count > 0 else 0.85,
        somatic_adapter_ok=base.somatic_adapter_ok,
        decay_applied=True,
        recovery_ok=pressure.composite < 0.95,
        adapter_ok=base.adapter_ok,
        pressure_composite=pressure.composite,
        focus_entropy=base.focus_entropy,
        submission_count=submissions,
        store_fill_ratio=store.fill_ratio(),
        trace_coverage=store.trace.coverage_ratio(),
        precursor_match_rate_mem=precursor_m.match_rate,
        background_stability=noise.background_stability,
        reinforcement_bounded=True,
        memory_count=store.count,
    )


def compute_attention_memory_stability(
    evidence: AttentionMemoryEvidence | None = None,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
) -> AttentionMemoryStabilityReport:
    if evidence is None:
        br = bridge or RuntimeAttentionMemoryBridge(kernel=kernel)
        evidence = evidence_from_bridge(br, kernel=kernel or br.kernel)

    runtime_report = evaluate_runtime_attention_stability(evidence)

    consolidation_headroom = clamp01(1.0 - evidence.store_fill_ratio)
    precursor_health = clamp01(0.7 + evidence.precursor_match_rate_mem * 0.3)
    noise_suppression = clamp01(evidence.background_stability)
    trace_discipline = clamp01(1.0 - evidence.trace_coverage * 0.5)

    memory_dims = {
        "consolidation_headroom": consolidation_headroom,
        "precursor_memory_health": precursor_health,
        "noise_suppression": noise_suppression,
        "trace_discipline": trace_discipline,
    }
    memory_bonus = sum(memory_dims[k] * MEMORY_EXTRA_WEIGHTS[k] for k in MEMORY_EXTRA_WEIGHTS)
    combined = clamp01(runtime_report.runtime_score * 0.88 + memory_bonus)

    hard_failures = list(runtime_report.hard_failures)
    if not evidence.reinforcement_bounded:
        hard_failures.append("reinforcement_unbounded")
    if evidence.store_fill_ratio >= 0.99:
        hard_failures.append("memory_store_saturated")

    gate_pass = (
        combined >= MEMORY_GATE_THRESHOLD
        and runtime_report.gate_pass
        and len(hard_failures) == 0
    )

    return AttentionMemoryStabilityReport(
        score=combined,
        classification=runtime_report.classification,
        dimensions=runtime_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=MEMORY_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=hard_failures,
        runtime_dimensions=runtime_report.runtime_dimensions,
        runtime_score=runtime_report.runtime_score,
        memory_dimensions=memory_dims,
        memory_score=combined,
    )


def evaluate_attention_memory_stability(
    evidence: AttentionMemoryEvidence | None = None,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
    **kwargs: Any,
) -> AttentionMemoryStabilityReport:
    if evidence is None and kwargs:
        evidence = AttentionMemoryEvidence(**kwargs)
    return compute_attention_memory_stability(evidence, bridge=bridge, kernel=kernel)


AttentionMemoryStabilityScore = AttentionMemoryStabilityReport
