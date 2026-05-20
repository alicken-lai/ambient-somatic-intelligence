"""Bounded ontology evolution — capped store with decay, not immutable ontology."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.meaning.meaning_record import MeaningRecord

_MAX_RECORDS = 128


@dataclass
class BoundedOntologyVerdict:
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


class BoundedOntologyEvolution:
    def __init__(self) -> None:
        self._records: list[MeaningRecord] = []

    def store(self, record: MeaningRecord) -> BoundedOntologyVerdict:
        issues: list[str] = []
        if record.retention_hours > 8760 * 5:
            issues.append("retention_too_long")
        lower = record.summary.lower()
        if "immutable ontology" in lower:
            issues.append("immutable_ontology")
        if len(self._records) >= _MAX_RECORDS:
            self._records.pop(0)
        self._records.append(record)
        return BoundedOntologyVerdict(
            stored=True,
            count=len(self._records),
            bounded=len(self._records) <= _MAX_RECORDS and not issues,
            issues=issues,
        )

    @property
    def records(self) -> list[MeaningRecord]:
        return list(self._records)
