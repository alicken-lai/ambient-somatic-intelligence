"""Area 9–10: RuntimeAttentionStabilityScore gate."""

from observability.v051.runtime_attention_stability_score import (
    RUNTIME_GATE_THRESHOLD,
    RuntimeAttentionEvidence,
    evaluate_runtime_attention_stability,
    evidence_from_kernel,
)
from attention.kernel.attention_kernel import AttentionKernel


def test_gate_threshold_090() -> None:
    assert RUNTIME_GATE_THRESHOLD == 0.90


def test_clean_evidence_passes() -> None:
    ev = RuntimeAttentionEvidence(
        explainability_coverage=1.0,
        competition_fairness=0.88,
        adapter_ok=True,
        pressure_composite=0.2,
    )
    report = evaluate_runtime_attention_stability(ev)
    assert report.runtime_score >= 0.90
    assert report.gate_pass is True


def test_kernel_evidence_from_simulation() -> None:
    kernel = AttentionKernel()
    ev = evidence_from_kernel(kernel)
    report = evaluate_runtime_attention_stability(ev, kernel=kernel)
    assert report.runtime_score >= 0.85
