"""
Salience vector — weighted multi-dimensional salience for a single target.

A :class:`SalienceVector` holds the per-dimension salience scores for one
attention target and exposes a single scalar ``total`` derived from the
canonical weighting in :mod:`attention.core.salience_factor`.

The total is computed lazily from the *current* dimension values, so mutating
``dimensions`` (e.g. when a decay process reduces ``urgency``) is immediately
reflected in ``total``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from attention.core.salience_factor import DEFAULT_DIMENSION_WEIGHTS


def _clamp_unit(value: float) -> float:
    """Clamp *value* into the closed unit interval ``[0.0, 1.0]``."""
    return max(0.0, min(1.0, float(value)))


def compute_weighted_salience(
    dimensions: dict[str, float],
    weights: Optional[dict[str, float]] = None,
) -> float:
    """
    Combine per-dimension scores into a single salience in ``[0.0, 1.0]``.

    Each dimension value is clamped to the unit interval and multiplied by its
    weight; dimensions absent from *weights* contribute nothing.  When *weights*
    is omitted the canonical :data:`DEFAULT_DIMENSION_WEIGHTS` is used.
    """
    if weights is None:
        weights = DEFAULT_DIMENSION_WEIGHTS
    total = sum(
        weights.get(name, 0.0) * _clamp_unit(value)
        for name, value in dimensions.items()
    )
    return _clamp_unit(total)


@dataclass
class SalienceVector:
    """Per-dimension salience scores for a single attention target."""

    target_id: str
    dimensions: dict[str, float] = field(default_factory=dict)
    weights: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_DIMENSION_WEIGHTS),
    )

    @property
    def total(self) -> float:
        """Weighted scalar salience computed from the current dimensions."""
        return compute_weighted_salience(self.dimensions, self.weights)

    def scale(self, factor: float) -> None:
        """Multiply every dimension by *factor*, clamping into ``[0, 1]``."""
        self.dimensions = {
            name: _clamp_unit(value * factor)
            for name, value in self.dimensions.items()
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict."""
        return {
            "target_id": self.target_id,
            "dimensions": {k: round(v, 4) for k, v in self.dimensions.items()},
            "total": round(self.total, 4),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SalienceVector":
        """Reconstruct from a serialised dict (weights default to canonical)."""
        return cls(
            target_id=data["target_id"],
            dimensions=dict(data.get("dimensions", {})),
            weights=dict(data.get("weights", DEFAULT_DIMENSION_WEIGHTS)),
        )
