"""Area 5: runtime memory bridge."""

from attention.core.attention_target import AttentionTarget


def test_bridge_ingest(memory_bridge) -> None:
    t = AttentionTarget("telemetry", "alert", 0.7, metadata={"tags": ["ops"]})
    r = memory_bridge.ingest_target(t)
    assert "memory_id" in r
    assert memory_bridge.store.count >= 1


def test_consolidated_activation(memory_bridge) -> None:
    r = memory_bridge.activate_consolidated("tid-1", "telemetry", 0.65)
    assert "memory" in r
    assert "activation" in r
