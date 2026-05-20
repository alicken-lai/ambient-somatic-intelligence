"""Entropy metric definitions — observable system drift signals."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MetricKind(str, Enum):
    """Categories of entropy observables."""

    DRIFT = "drift"
    COUPLING = "coupling"
    MUTATION = "mutation"
    PATCH = "patch"
    ORPHAN = "orphan"
    STALE = "stale"


@dataclass
class EntropyMetric:
    """
    A single observable entropy signal.

    Metrics are read-only observations — they never mutate subsystem state.
    """

    name: str
    kind: MetricKind
    value: float  # normalised 0.0–1.0
    weight: float = 1.0
    source: str = ""
    detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"EntropyMetric.value must be 0.0–1.0, got {self.value}")
        if self.weight < 0.0:
            raise ValueError("EntropyMetric.weight must be non-negative")

    def weighted_value(self) -> float:
        return self.value * self.weight

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind.value,
            "value": round(self.value, 4),
            "weight": self.weight,
            "source": self.source,
            "detail": self.detail,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MetricSnapshot:
    """Point-in-time collection of entropy metrics."""

    metrics: tuple[EntropyMetric, ...]
    captured_at: str

    def by_kind(self, kind: MetricKind) -> list[EntropyMetric]:
        return [m for m in self.metrics if m.kind == kind]

    def to_dict(self) -> dict[str, Any]:
        return {
            "captured_at": self.captured_at,
            "metric_count": len(self.metrics),
            "metrics": [m.to_dict() for m in self.metrics],
        }
