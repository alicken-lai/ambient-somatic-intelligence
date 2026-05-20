"""Area 3: somatic adapter."""

from attention.attention_state import AttentionSignal
from attention.somatic.somatic_attention_adapter import SomaticAttentionAdapter


def test_adapter_from_legacy_signal() -> None:
    adapter = SomaticAttentionAdapter()
    adapter.update_stress(0.7)
    sig = AttentionSignal("somatic", "heat", 0.6)
    target = adapter.from_signal(sig)
    assert target.metadata.get("somatic_severity", 0) > 0
