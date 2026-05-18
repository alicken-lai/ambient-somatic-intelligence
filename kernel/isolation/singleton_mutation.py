"""Singleton mutation record — audit trail for governed singleton writes."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class SingletonMutation:
    singleton: str
    attribute: str | None = None
    context_id: str | None = None
    caller_id: str | None = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "singleton": self.singleton,
            "attribute": self.attribute,
            "context_id": self.context_id,
            "caller_id": self.caller_id,
            "timestamp": self.timestamp,
        }
