"""Bounded normative evolution — capped store with decay, not immutable ethics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.value.value_record import ValueRecord

_MAX_RECORDS = 128


@dataclass
class BoundedNormativeVerdict:
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


class BoundedNormativeEvolution:
    def __init__(self) -> None:
        self._records: list[ValueRecord] = []

    def store(self, record: ValueRecord) -> BoundedNormativeVerdict:
        issues: list[str] = []
        if record.retention_hours > 8760 * 5:
            issues.append("retention_too_long")
        lower = record.summary.lower()
        if "immutable ethics" in lower:
            issues.append("immutable_ethics")
        if len(self._records) >= _MAX_RECORDS:
            self._records.pop(0)
        self._records.append(record)
        return BoundedNormativeVerdict(
            stored=True,
            count=len(self._records),
            bounded=len(self._records) <= _MAX_RECORDS and not issues,
            issues=issues,
        )

    @property
    def records(self) -> list[ValueRecord]:
        return list(self._records)
