"""Area 4: somatic runtime bridge."""

from datetime import datetime, timezone

from attention.attention_state import AttentionSignal
from attention.somatic.runtime_somatic_attention import RuntimeSomaticAttention
from attention.somatic.somatic_runtime_bridge import SomaticRuntimeBridge


def test_somatic_submit(runtime_kernel) -> None:
    rt = RuntimeSomaticAttention(runtime_kernel, stress=0.3)
    sig = AttentionSignal(
        signal_id="s1",
        source_domain="somatic",
        signal_type="hrv_drop",
        raw_value=0.8,
        timestamp=datetime.now(timezone.utc),
    )
    assert rt.submit_signal(sig)["accepted"] is True


def test_somatic_payload_bridge(runtime_kernel) -> None:
    bridge = SomaticRuntimeBridge(RuntimeSomaticAttention(runtime_kernel))
    r = bridge.from_payload({"severity": 0.7, "stress": 0.4})
    assert r["accepted"] is True
