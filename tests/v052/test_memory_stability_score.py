"""Area 10: AttentionMemoryStabilityScore gate."""

from observability.v052.attention_memory_stability_score import (
    MEMORY_GATE_THRESHOLD,
    AttentionMemoryEvidence,
    evaluate_attention_memory_stability,
)


def test_gate_threshold_090() -> None:
    assert MEMORY_GATE_THRESHOLD == 0.90


def test_clean_evidence_passes() -> None:
    ev = AttentionMemoryEvidence(
        explainability_coverage=1.0,
        competition_fairness=0.88,
        adapter_ok=True,
        pressure_composite=0.2,
        store_fill_ratio=0.1,
        trace_coverage=0.2,
        background_stability=0.95,
        reinforcement_bounded=True,
    )
    report = evaluate_attention_memory_stability(ev)
    assert report.memory_score >= 0.90
    assert report.gate_pass is True


def test_bridge_evidence(memory_bridge) -> None:
    from observability.v052.attention_memory_stability_score import evidence_from_bridge

    ev = evidence_from_bridge(memory_bridge)
    report = evaluate_attention_memory_stability(ev, bridge=memory_bridge)
    assert report.memory_score >= 0.85
