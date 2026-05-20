"""Registry mutation record — audit trail for governed registry writes."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class RegistryMutation:
    registry: str
    operation: str
    write_target: str
    context_id: str | None = None
    caller_id: str | None = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "registry": self.registry,
            "operation": self.operation,
            "write_target": self.write_target,
            "context_id": self.context_id,
            "caller_id": self.caller_id,
            "timestamp": self.timestamp,
        }
