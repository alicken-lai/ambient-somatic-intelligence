"""
Precursor weighting — bounded influence of a precursor signal.

Converts a :class:`PrecursorSignal` into a weight in ``[0, 1]`` that the
forecasting layer applies when projecting future salience.  Stronger precursors
weigh more, but the weight is always bounded by 1.0.
"""

from __future__ import annotations

from attention.core.precursor_signal import PrecursorSignal


class PrecursorWeighting:
    """Maps a precursor signal to a bounded influence weight."""

    def __init__(self, floor: float = 0.1) -> None:
        self.floor = max(0.0, min(1.0, float(floor)))

    def weight(self, precursor: PrecursorSignal) -> float:
        """Return a weight in ``[floor, 1.0]`` based on precursor strength."""
        strength = max(0.0, min(1.0, precursor.strength))
        return max(self.floor, min(1.0, strength))
