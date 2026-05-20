"""Area 4: attention pathology signals."""

from governance.metacognition.attention_pathology import AttentionPathology


def test_normal_entropy_low_pressure() -> None:
    ap = AttentionPathology()
    assert ap.pressure(focus_entropy=0.5, submission_count=3) < 0.35


def test_fixation_label() -> None:
    ap = AttentionPathology()
    labels = ap.labels(focus_entropy=0.1, submission_count=10)
    assert "attention_fixation" in labels


def test_budget_overrun_pressure() -> None:
    ap = AttentionPathology()
    assert ap.pressure(budget_overrun=True) >= 0.3
