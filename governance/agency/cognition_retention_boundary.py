"""Cognition retention boundary — cap advisory agency retention windows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_MAX_RETENTION_HOURS = 8760.0


@dataclass
class CognitionRetentionBoundaryVerdict:
    within_bounds: bool
    retention_hours: float = 168.0
    capped_hours: float = 168.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "within_bounds": self.within_bounds,
            "retention_hours": round(self.retention_hours, 2),
            "capped_hours": round(self.capped_hours, 2),
        }


class CognitionRetentionBoundary:
    def bound(self, retention_hours: float) -> CognitionRetentionBoundaryVerdict:
        capped = min(max(1.0, retention_hours), _MAX_RETENTION_HOURS)
        return CognitionRetentionBoundaryVerdict(
            within_bounds=retention_hours <= _MAX_RETENTION_HOURS and retention_hours >= 1.0,
            retention_hours=retention_hours,
            capped_hours=capped,
        )
