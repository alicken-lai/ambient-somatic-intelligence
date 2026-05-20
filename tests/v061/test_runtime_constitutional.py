"""Area 5: runtime constitutional wire."""

from attention.core.attention_target import AttentionTarget


def test_submit_governed_includes_constitutional(constitutional_activation) -> None:
    t = AttentionTarget("telemetry", "const-runtime", 0.55)
    out = constitutional_activation.submit_governed_target(t, raw_confidence=0.75)
    assert out.get("accepted") is True or "governance" in out
    if out.get("governed"):
        assert "governance" in out
