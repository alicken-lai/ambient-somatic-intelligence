"""Continuity retention policy — bounded horizons without immortal cognition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_MAX_RETENTION_HOURS = 8760.0


@dataclass
class ContinuityRetentionVerdict:
    retention_ok: bool
    retention_hours: float = 168.0
    issues: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "retention_ok": self.retention_ok,
            "retention_hours": round(self.retention_hours, 2),
            "issues": list(self.issues or []),
        }


class ContinuityRetention:
    def evaluate(self, *, retention_hours: float = 168.0) -> ContinuityRetentionVerdict:
        issues: list[str] = []
        if retention_hours > _MAX_RETENTION_HOURS:
            issues.append("retention_exceeds_cap")
        if retention_hours <= 0:
            issues.append("invalid_retention")
        return ContinuityRetentionVerdict(
            retention_ok=len(issues) == 0,
            retention_hours=retention_hours,
            issues=issues or None,
        )
