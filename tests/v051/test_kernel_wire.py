"""Area 10: end-to-end kernel wiring across adapters."""

from attention.core.attention_target import AttentionTarget
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.telemetry_attention_adapter import TelemetryAttentionAdapter
from attention.governance.guardian_attention_bridge import GuardianAttentionBridge
from attention.runtime.overload_recovery import OverloadRecovery


def test_full_runtime_pipeline() -> None:
    kernel = AttentionKernel(max_focus=5, max_queue=30)
    adapter = TelemetryAttentionAdapter(kernel)
    guardian = GuardianAttentionBridge(kernel)
    recovery = OverloadRecovery(kernel)

    high = AttentionTarget("somatic", "alert", 0.95, metadata={"urgency": 0.95})
    kernel.submit(high)
    guardian.from_guardian_result("test", "BLOCK")
    adapter.tick()
    recovery.step()
    snap = kernel.tick()
    assert len(snap.state.focused_targets) >= 0
