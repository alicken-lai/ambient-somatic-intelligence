"""Divergence record — cross-runtime truth delta without merge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DivergenceRecord:
    """Captures divergence between sovereign operational realities."""

    left_runtime: str
    right_runtime: str
    divergence_score: float
    signals: list[str] = field(default_factory=list)
    merge_forbidden: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "left_runtime": self.left_runtime,
            "right_runtime": self.right_runtime,
            "divergence_score": round(self.divergence_score, 4),
            "signals": list(self.signals),
            "merge_forbidden": self.merge_forbidden,
        }
