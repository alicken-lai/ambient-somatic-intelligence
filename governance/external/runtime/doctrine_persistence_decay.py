"""Decay external doctrine persistence so runtime soak cannot cement bad state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_INITIAL_WEIGHT = 1.0
_DECAY_FACTOR = 0.92
_MIN_WEIGHT = 0.15


@dataclass
class PersistenceDecayState:
    weight: float
    cycles: int
    decayed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "weight": round(self.weight, 4),
            "cycles": self.cycles,
            "decayed": self.decayed,
        }


class DoctrinePersistenceDecay:
    def __init__(
        self,
        *,
        decay_factor: float = _DECAY_FACTOR,
        min_weight: float = _MIN_WEIGHT,
    ) -> None:
        self._decay_factor = decay_factor
        self._min_weight = min_weight
        self._weight = _INITIAL_WEIGHT
        self._cycles = 0

    def tick(self, *, reinforced: bool = False) -> PersistenceDecayState:
        self._cycles += 1
        if reinforced:
            self._weight = min(1.0, self._weight + 0.05)
        else:
            self._weight = max(self._min_weight, self._weight * self._decay_factor)
        return PersistenceDecayState(
            weight=self._weight,
            cycles=self._cycles,
            decayed=self._weight <= self._min_weight + 0.01,
        )

    @property
    def current_weight(self) -> float:
        return self._weight
