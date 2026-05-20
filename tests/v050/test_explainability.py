"""Area 7: explainability."""

from attention.core.attention_target import AttentionTarget
from attention.explainability.explain_attention import explain_attention
from attention.kernel.salience_engine import KernelSalienceEngine


def test_explain_attention_has_breakdown() -> None:
    engine = KernelSalienceEngine()
    target = AttentionTarget("governance", "alert", 0.8)
    result = engine.compute(target)
    expl = explain_attention(result)
    assert expl.dominant_factor is not None
    assert len(expl.breakdown.children) == 10
