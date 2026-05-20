"""Area 8: observability metrics."""

from attention.core.attention_state import AttentionKernelState
from attention.kernel.attention_queue import AttentionQueue
from observability.v05.attention_metrics import collect_attention_metrics
from observability.v05.attention_pressure import compute_attention_pressure
from observability.v05.salience_distribution import compute_distribution
from attention.core.salience import SalienceVector


def test_metrics_and_pressure() -> None:
    state = AttentionKernelState()
    state.salience_by_target["a"] = SalienceVector("a", {"urgency": 0.8})
    m = collect_attention_metrics(state, AttentionQueue())
    p = compute_attention_pressure(m)
    assert p.composite >= 0
    dist = compute_distribution(list(state.salience_by_target.values()))
    assert dist.count == 1
