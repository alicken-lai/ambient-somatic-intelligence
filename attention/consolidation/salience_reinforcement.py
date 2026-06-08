"""
Salience reinforcement — bounded strengthening of repeatedly-confirmed salience.

Repeated confirmation should raise a memory's salience, but never to absolute
certainty.  Reinforcement asymptotically approaches :data:`REINFORCEMENT_CEILING`
and can never exceed it — this is the consolidation-layer expression of the
"no overconfident memory" doctrine.
"""

from __future__ import annotations

import math

# Hard ceiling on reinforced salience: confirmation never yields certainty.
REINFORCEMENT_CEILING: float = 0.95


class SalienceReinforcement:
    """Strengthens salience toward a bounded ceiling with diminishing returns."""

    def __init__(self, ceiling: float = REINFORCEMENT_CEILING, saturation: float = 50.0) -> None:
        self.ceiling = max(0.0, min(1.0, float(ceiling)))
        self.saturation = max(1e-6, float(saturation))

    def reinforce(self, current: float, evidence: float, hit_count: int = 0) -> float:
        """Return reinforced salience, capped at :attr:`ceiling`."""
        current = max(0.0, min(1.0, float(current)))
        evidence = max(0.0, min(1.0, float(evidence)))
        gain = (1.0 - current) * evidence * (1.0 - math.exp(-max(0, hit_count) / self.saturation))
        return min(self.ceiling, current + gain)
