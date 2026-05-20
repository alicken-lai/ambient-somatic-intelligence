"""Typed signal contracts for somatic ↔ stabilization bridges."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SignalContract:
    """Contract for signals crossing subsystem boundaries."""

    name: str
    signal_type: str
    source_domain: str
    normalised_range: tuple[float, float] = (0.0, 1.0)
    required_metadata: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""

    def validate(self, raw_value: float, metadata: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        lo, hi = self.normalised_range
        if not lo <= raw_value <= hi:
            errors.append(f"raw_value {raw_value} outside [{lo}, {hi}]")
        for key in self.required_metadata:
            if key not in metadata:
                errors.append(f"missing metadata key: {key}")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "signal_type": self.signal_type,
            "source_domain": self.source_domain,
            "normalised_range": list(self.normalised_range),
            "required_metadata": list(self.required_metadata),
            "description": self.description,
        }


V04_SIGNAL_CONTRACTS: tuple[SignalContract, ...] = (
    SignalContract(
        name="entropy_pressure_signal",
        signal_type="entropy_pressure",
        source_domain="kernel.entropy",
        description="Entropy score elevated — forwarded to somatic bus for visibility.",
        required_metadata=("score", "classification"),
    ),
    SignalContract(
        name="truth_conflict_signal",
        signal_type="truth_conflict",
        source_domain="kernel.truth",
        description="Truth graph conflict detected — observability only.",
        required_metadata=("conflict_count",),
    ),
)

SIGNAL_CONTRACT_MAP: dict[str, SignalContract] = {
    c.name: c for c in V04_SIGNAL_CONTRACTS
}
