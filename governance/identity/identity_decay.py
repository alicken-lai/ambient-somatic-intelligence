"""Identity decay — gentle authority reduction as registry grows."""

from __future__ import annotations

from observability.v04.metric_normalizer import clamp01

DECAY_START = 80
DECAY_FLOOR = 0.88


class IdentityDecay:
    def multiplier(self, registry_size: int) -> float:
        if registry_size <= DECAY_START:
            return 1.0
        excess = registry_size - DECAY_START
        return clamp01(max(DECAY_FLOOR, 1.0 - excess * 0.001))
