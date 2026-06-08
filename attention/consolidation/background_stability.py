"""
Background stability — how settled the ambient attention background is.

A stable background is one with a well-characterised set of benign patterns and
a trace that isn't saturated with churn.  The score is in ``[0, 1]``: higher
means a calmer, better-understood background.
"""

from __future__ import annotations

from attention.consolidation.attention_trace import AttentionTrace
from attention.consolidation.benign_pattern_memory import BenignPatternMemory


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class BackgroundStability:
    """Scores how stable the ambient attention background is."""

    def __init__(self, baseline: float = 0.8) -> None:
        self.baseline = _clamp_unit(baseline)

    def score(self, trace: AttentionTrace, benign: BenignPatternMemory) -> float:
        """Return a background-stability score in ``[0, 1]``."""
        trace_load = trace.coverage_ratio()
        benign_ratio = benign.count / max(1, benign.max_patterns)
        return _clamp_unit(self.baseline + 0.2 * benign_ratio - 0.2 * trace_load)
