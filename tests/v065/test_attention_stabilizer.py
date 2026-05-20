"""Area 3: attention stabilizer."""

from governance.homeostasis.attention_stabilizer import AttentionStabilizer


def test_low_entropy_no_recommendations() -> None:
    s = AttentionStabilizer()
    assert s.recommend(focus_entropy=0.4, budget_overrun=False) == []


def test_high_entropy_recommends() -> None:
    s = AttentionStabilizer()
    recs = s.recommend(focus_entropy=0.8, budget_overrun=True)
    assert len(recs) >= 1
