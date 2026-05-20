"""Bounded civilization memory — capped store with decay, not permanent federation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.temporal.continuity_record import ContinuityRecord

_MAX_RECORDS = 128


@dataclass
class BoundedMemoryVerdict:
    stored: bool
    count: int = 0
    bounded: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stored": self.stored,
            "count": self.count,
            "bounded": self.bounded,
            "issues": list(self.issues),
        }


class BoundedCivilizationMemory:
    def __init__(self) -> None:
        self._records: list[ContinuityRecord] = []

    def store(self, record: ContinuityRecord) -> BoundedMemoryVerdict:
        issues: list[str] = []
        if record.retention_hours > 8760 * 5:
            issues.append("retention_too_long")
        if len(self._records) >= _MAX_RECORDS:
            self._records.pop(0)
        self._records.append(record)
        return BoundedMemoryVerdict(
            stored=True,
            count=len(self._records),
            bounded=len(self._records) <= _MAX_RECORDS and not issues,
            issues=issues,
        )

    @property
    def records(self) -> list[ContinuityRecord]:
        return list(self._records)
