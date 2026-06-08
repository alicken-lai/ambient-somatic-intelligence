"""
attention.kernel — scoring, queueing and focus selection.

Builds directly on :mod:`attention.core`:

- :class:`KernelSalienceEngine` — scores a target into a 10-dim vector
- :class:`AttentionQueue`       — bounded, salience-ordered pending queue
- :class:`AttentionKernel`      — submit / tick orchestration
- :class:`KernelTickResult`     — the per-tick snapshot
"""

from attention.kernel.attention_kernel import AttentionKernel, KernelTickResult
from attention.kernel.attention_queue import AttentionQueue
from attention.kernel.salience_engine import KernelSalienceEngine

__all__ = [
    "AttentionKernel",
    "KernelTickResult",
    "AttentionQueue",
    "KernelSalienceEngine",
]
