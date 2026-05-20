"""Area 9: AttentionStabilityScore gate."""

from observability.v05.attention_stability_score import (
    ATTENTION_GATE_THRESHOLD,
    AttentionRuntimeEvidence,
    compute_attention_stability,
)


def test_gate_threshold_is_090() -> None:
    assert ATTENTION_GATE_THRESHOLD == 0.90


def test_clean_evidence_passes_gate() -> None:
    ev = AttentionRuntimeEvidence(competition_fairness=0.85)
    report = compute_attention_stability(ev)
    assert report.score >= 0.90
    assert report.gate_pass is True


def test_opaque_salience_blocks_gate() -> None:
    ev = AttentionRuntimeEvidence(opaque_salience_count=1)
    report = compute_attention_stability(ev)
    assert report.gate_pass is False
    assert "opaque_salience" in report.hard_failures[0]
