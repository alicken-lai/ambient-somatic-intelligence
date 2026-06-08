"""
Attention memory — a single consolidated memory of a salient target.

When a target has been attended to enough, the store consolidates it into an
:class:`AttentionMemory` record that captures the peak salience it reached and
how many trace events contributed to it.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AttentionMemory:
    """A consolidated memory of an attended target."""

    target_id: str
    domain: str
    salience_peak: float = 0.0
    salience_mean: float = 0.0
    trace_count: int = 0
    memory_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "target_id": self.target_id,
            "domain": self.domain,
            "salience_peak": round(self.salience_peak, 4),
            "salience_mean": round(self.salience_mean, 4),
            "trace_count": self.trace_count,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
