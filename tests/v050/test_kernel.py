"""Area 2: attention kernel orchestration."""

from attention.core.attention_target import AttentionTarget
from attention.kernel.attention_kernel import AttentionKernel


def test_kernel_submit_and_tick(attention_kernel: AttentionKernel, somatic_target: AttentionTarget) -> None:
    r = attention_kernel.submit(somatic_target)
    assert r["accepted"] is True
    snap = attention_kernel.tick()
    assert len(snap.state.focused_targets) >= 0


def test_high_salience_beats_low(attention_kernel: AttentionKernel) -> None:
    low = AttentionTarget("task", "routine", 0.05)
    high = AttentionTarget("somatic", "alert", 0.95, metadata={"urgency": 0.95})
    attention_kernel.submit(low)
    attention_kernel.submit(high)
    snap = attention_kernel.tick()
    if snap.focused_salience:
        assert max(snap.focused_salience.values()) >= 0.3
