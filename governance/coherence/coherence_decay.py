"""Coherence decay — gentle score reduction as registry grows."""

from __future__ import annotations

from observability.v04.metric_normalizer import clamp01

DECAY_START = 100
DECAY_FLOOR = 0.90


class CoherenceDecay:
    def multiplier(self, evaluation_count: int) -> float:
        if evaluation_count <= DECAY_START:
            return 1.0
        excess = evaluation_count - DECAY_START
        return clamp01(max(DECAY_FLOOR, 1.0 - excess * 0.0008))
