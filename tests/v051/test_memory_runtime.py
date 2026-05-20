"""Area 3: bounded memory activation."""

from attention.core.attention_target import AttentionTarget
from attention.runtime.runtime_memory_activation import RuntimeMemoryActivation
from attention.runtime.precursor_memory_bridge import PrecursorMemoryBridge
from attention.core.precursor_signal import PrecursorSignal


def test_memory_activation_cap(runtime_kernel) -> None:
    act = RuntimeMemoryActivation(runtime_kernel, max_activations=2)
    t = AttentionTarget("memory", "recall", 0.6, metadata={"tags": ["a"], "memory_relevance": 0.5})
    act.activate(t, ["a"])
    act.activate(t, ["a"])
    third = act.activate(t, ["a"])
    assert third["accepted"] is False
    assert third["reason"] == "activation_cap_reached"


def test_precursor_bridge(runtime_kernel) -> None:
    bridge = PrecursorMemoryBridge(RuntimeMemoryActivation(runtime_kernel))
    p = PrecursorSignal(
        pattern_id="pat-1",
        strength=0.6,
        domain="somatic",
        metadata={"tags": ["alert"]},
    )
    r = bridge.from_precursor(p, recent_tags=["alert"])
    assert r.get("accepted") is True or "activation_level" in r
