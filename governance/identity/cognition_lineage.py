"""Cognition lineage — append-only provenance chain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.identity.provenance_record import ProvenanceRecord


@dataclass
class CognitionLineage:
    records: list[ProvenanceRecord] = field(default_factory=list)

    def append(self, record: ProvenanceRecord) -> None:
        self.records.append(record)

    def chain_tail(self, n: int = 5) -> list[str]:
        return [r.identity_signature for r in self.records[-n:]]

    def verify_chain(self) -> bool:
        if len(self.records) < 2:
            return True
        for prev, cur in zip(self.records, self.records[1:]):
            if cur.corrupted or prev.corrupted:
                return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "length": len(self.records),
            "chain_verified": self.verify_chain(),
            "tail_origins": [r.origin.value for r in self.records[-5:]],
        }
