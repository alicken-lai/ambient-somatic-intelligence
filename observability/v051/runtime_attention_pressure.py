"""Runtime attention pressure from kernel state."""

from __future__ import annotations

from attention.kernel.attention_kernel import AttentionKernel
from observability.v05.attention_pressure import AttentionPressure, compute_attention_pressure
from observability.v051.runtime_attention_metrics import collect_runtime_attention_metrics


def compute_runtime_attention_pressure(kernel: AttentionKernel) -> AttentionPressure:
    metrics = collect_runtime_attention_metrics(kernel)
    max_queue = getattr(kernel.queue, "max_size", None) or getattr(kernel.queue, "_max_size", 100)
    return compute_attention_pressure(
        metrics,
        max_focus=kernel.allocator.max_slots,
        max_queue=max_queue,
    )
