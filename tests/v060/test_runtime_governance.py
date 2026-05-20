"""Area 5: governed runtime wire."""

from attention.core.attention_target import AttentionTarget


def test_submit_governed_target(governed_activation) -> None:
    t = AttentionTarget("telemetry", "gov-runtime", 0.52)
    result = governed_activation.submit_governed_target(t, raw_confidence=0.78)
    assert result.get("governed") is True or result.get("accepted") is False
    if result.get("governed"):
        assert "governance" in result
