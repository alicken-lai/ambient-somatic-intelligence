"""
Attention target — a domain-agnostic candidate for the attention layer.

An :class:`AttentionTarget` is what any subsystem (somatic, governance, memory,
telemetry, task, external) submits to the attention kernel.  It mirrors the
shape of :class:`attention.attention_state.AttentionSignal` but carries a stable
``target_id`` and an optional attached :class:`SalienceVector`, which the kernel
and forecasting layers populate as the target is scored.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from attention.core.salience import SalienceVector


@dataclass
class AttentionTarget:
    """A unified, domain-agnostic attention candidate."""

    source_domain: str
    signal_type: str
    raw_value: float
    metadata: dict[str, Any] = field(default_factory=dict)
    target_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    source_ref: Optional[str] = None
    salience: Optional[SalienceVector] = None
    precursor_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.raw_value = max(0.0, min(1.0, float(self.raw_value)))
        if self.metadata is None:
            self.metadata = {}

    @property
    def age_seconds(self) -> float:
        """Seconds elapsed since the target was created."""
        return (datetime.now(timezone.utc) - self.timestamp).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict."""
        return {
            "target_id": self.target_id,
            "source_domain": self.source_domain,
            "signal_type": self.signal_type,
            "raw_value": round(self.raw_value, 4),
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "source_ref": self.source_ref,
            "salience": self.salience.to_dict() if self.salience else None,
            "precursor_refs": list(self.precursor_refs),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AttentionTarget":
        """Reconstruct from a serialised dict."""
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        elif ts is None:
            ts = datetime.now(timezone.utc)
        salience_data = data.get("salience")
        return cls(
            source_domain=data["source_domain"],
            signal_type=data["signal_type"],
            raw_value=float(data["raw_value"]),
            metadata=dict(data.get("metadata", {})),
            target_id=data.get("target_id", uuid.uuid4().hex),
            timestamp=ts,
            source_ref=data.get("source_ref"),
            salience=SalienceVector.from_dict(salience_data) if salience_data else None,
            precursor_refs=list(data.get("precursor_refs", [])),
        )
