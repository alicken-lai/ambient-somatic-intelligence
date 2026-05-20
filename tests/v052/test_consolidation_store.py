"""Area 1: bounded consolidation store."""

from attention.consolidation.attention_memory_store import AttentionMemoryStore


def test_store_bounded_eviction() -> None:
    store = AttentionMemoryStore(max_entries=3)
    for i in range(5):
        store.trace.append(f"t{i}", "telemetry", 0.5)
        store.history.record(f"t{i}", 0.5)
        store.consolidate(f"t{i}", "telemetry")
    assert store.count <= 3


def test_trace_ring_cap() -> None:
    from attention.consolidation.attention_trace import AttentionTrace

    trace = AttentionTrace(max_entries=10)
    store = AttentionMemoryStore(trace=trace)
    for i in range(20):
        store.trace.append(f"x{i}", "d", 0.1)
    assert store.trace.count == 10
