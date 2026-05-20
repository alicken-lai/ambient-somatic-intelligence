"""Area 4: memory activation."""

from attention.core.attention_target import AttentionTarget
from attention.memory.recall_salience import RecallSalience


def test_recall_salience_with_tags() -> None:
    rs = RecallSalience()
    rs.resonance.record("memory", "recall_hit", 0.9)
    t = AttentionTarget("memory", "recall_hit", 0.5, metadata={"tags": ["a", "b"]})
    score = rs.score(t, recent_tags=["a"])
    assert score > 0
