"""Area 2: governance / guardian attention bridge."""

from attention.governance.escalation_salience import escalation_boost
from attention.governance.guardian_attention_bridge import GuardianAttentionBridge
from attention.kernel.attention_kernel import AttentionKernel


def test_escalation_boost_ordering() -> None:
    assert escalation_boost("BLOCK") > escalation_boost("REVIEW_REQUIRED")
    assert escalation_boost("ALLOW") == 0.0


def test_guardian_bridge_submits(runtime_kernel: AttentionKernel) -> None:
    bridge = GuardianAttentionBridge(runtime_kernel)
    r = bridge.from_guardian_result("git push", "REVIEW_REQUIRED", matched=["git"])
    assert r["accepted"] is True
