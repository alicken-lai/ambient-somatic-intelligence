"""Interpretive retention — bounded retention policy for meaning records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_MAX_RETENTION_HOURS = 8760 * 2


@dataclass
class InterpretiveRetentionVerdict:
    retention_ok: bool
    max_hours: float = _MAX_RETENTION_HOURS
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "retention_ok": self.retention_ok,
            "max_hours": self.max_hours,
            "issues": list(self.issues),
        }


class InterpretiveRetention:
    def evaluate(self, retention_hours: float) -> InterpretiveRetentionVerdict:
        issues: list[str] = []
        if retention_hours > _MAX_RETENTION_HOURS:
            issues.append("retention_exceeds_bound")
        return InterpretiveRetentionVerdict(
            retention_ok=len(issues) == 0,
            issues=issues,
        )
