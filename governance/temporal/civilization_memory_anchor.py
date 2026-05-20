"""Civilization memory anchor — bounded anchors without permanent federation memory."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.temporal.continuity_record import ContinuityRecord
from observability.v04.metric_normalizer import clamp01

_MAX_ANCHORS = 64
_DEFAULT_RETENTION_HOURS = 168.0


@dataclass
class MemoryAnchorVerdict:
    anchored: bool
    anchor_count: int = 0
    retention_bounded: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "anchored": self.anchored,
            "anchor_count": self.anchor_count,
            "retention_bounded": self.retention_bounded,
            "issues": list(self.issues),
        }


class CivilizationMemoryAnchor:
    """Bounded in-process anchors — not permanent federation memory."""

    def __init__(self) -> None:
        self._anchors: list[ContinuityRecord] = []

    def anchor(self, record: ContinuityRecord) -> MemoryAnchorVerdict:
        issues: list[str] = []
        if record.retention_hours > 8760:
            issues.append("retention_exceeds_one_year")
        if len(self._anchors) >= _MAX_ANCHORS:
            self._anchors.pop(0)
        self._anchors.append(record)
        retention_bounded = record.retention_hours <= _DEFAULT_RETENTION_HOURS * 52
        return MemoryAnchorVerdict(
            anchored=True,
            anchor_count=len(self._anchors),
            retention_bounded=retention_bounded and not issues,
            issues=issues,
        )

    def fill_ratio(self) -> float:
        return clamp01(len(self._anchors) / _MAX_ANCHORS)
