"""
attention.core — foundational data structures for the attention architecture.

This is the lowest layer of the layered ``attention`` package.  It defines the
pure value/state objects that every higher layer (kernel, dynamics,
consolidation, forecasting, calibration, runtime, explainability) builds on:

- :class:`AttentionTarget`        — a domain-agnostic attention candidate
- :class:`SalienceVector`         — weighted multi-dimensional salience
- :class:`PrecursorSignal`        — a weak, early indicator
- :class:`AttentionKernelState`   — the kernel's mutable working state
- the canonical 10-dimension salience model (``ALL_DIMENSIONS`` etc.)
"""

from attention.core.attention_state import AttentionKernelState
from attention.core.attention_target import AttentionTarget
from attention.core.precursor_signal import PrecursorSignal
from attention.core.salience import SalienceVector, compute_weighted_salience
from attention.core.salience_factor import (
    ALL_DIMENSIONS,
    DEFAULT_DIMENSION_WEIGHTS,
)

__all__ = [
    "AttentionKernelState",
    "AttentionTarget",
    "PrecursorSignal",
    "SalienceVector",
    "compute_weighted_salience",
    "ALL_DIMENSIONS",
    "DEFAULT_DIMENSION_WEIGHTS",
]
