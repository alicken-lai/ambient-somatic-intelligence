"""Area 7: observability v051 metrics."""

from attention.kernel.attention_kernel import AttentionKernel
from observability.v051.runtime_attention_metrics import collect_runtime_attention_metrics
from observability.v051.runtime_attention_pressure import compute_runtime_attention_pressure
from observability.v051.runtime_focus_distribution import compute_runtime_focus_distribution
from observability.v051.precursor_attention_metrics import collect_precursor_metrics


def test_runtime_metrics_and_pressure(runtime_kernel: AttentionKernel) -> None:
    m = collect_runtime_attention_metrics(runtime_kernel)
    p = compute_runtime_attention_pressure(runtime_kernel)
    assert m.adapter_ok is True
    assert p.composite >= 0.0


def test_focus_distribution(runtime_kernel: AttentionKernel) -> None:
    dist = compute_runtime_focus_distribution(runtime_kernel)
    assert dist.total_focused >= 0
    prec = collect_precursor_metrics(runtime_kernel)
    assert prec.match_rate >= 0.0
