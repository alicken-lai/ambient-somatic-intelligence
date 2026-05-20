"""Area 5: coherence recovery."""

from governance.homeostasis.coherence_recovery import CoherenceRecovery


def test_healthy_coherence_no_gap() -> None:
    r = CoherenceRecovery()
    assert r.gap(coherence_score=0.85, coherence_ok=True) == 0.0


def test_low_coherence_recommends() -> None:
    r = CoherenceRecovery()
    recs = r.recommend(coherence_score=0.35, coherence_ok=False)
    assert len(recs) >= 1
