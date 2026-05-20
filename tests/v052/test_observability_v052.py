"""Area 7: observability v052 metrics."""

from attention.consolidation.attention_memory_store import AttentionMemoryStore
from observability.v052.consolidation_metrics import collect_consolidation_metrics
from observability.v052.memory_consolidation_pressure import compute_memory_consolidation_pressure
from observability.v052.noise_suppression_metrics import collect_noise_suppression_metrics
from attention.consolidation.benign_pattern_memory import BenignPatternMemory


def test_consolidation_metrics() -> None:
    store = AttentionMemoryStore()
    m = collect_consolidation_metrics(store)
    assert m.memory_count == 0


def test_memory_pressure() -> None:
    store = AttentionMemoryStore()
    p = compute_memory_consolidation_pressure(store)
    assert 0.0 <= p.composite <= 1.0


def test_noise_metrics() -> None:
    store = AttentionMemoryStore()
    m = collect_noise_suppression_metrics(BenignPatternMemory(), store.trace)
    assert m.background_stability >= 0.0
