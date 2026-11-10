"""Identity and narrative continuity models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class IdentityProfile:
    identity_id: str
    core_values: list[str] = field(default_factory=list)
    core_principles: list[str] = field(default_factory=list)
    long_term_objectives: list[str] = field(default_factory=list)
    governance_commitments: list[str] = field(default_factory=list)
    non_negotiable_constraints: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    last_updated: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "core_values": self.core_values,
            "core_principles": self.core_principles,
            "long_term_objectives": self.long_term_objectives,
            "governance_commitments": self.governance_commitments,
            "non_negotiable_constraints": self.non_negotiable_constraints,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "IdentityProfile":
        return cls(
            identity_id=str(raw["identity_id"]),
            core_values=list(raw.get("core_values", [])),
            core_principles=list(raw.get("core_principles", [])),
            long_term_objectives=list(raw.get("long_term_objectives", [])),
            governance_commitments=list(raw.get("governance_commitments", [])),
            non_negotiable_constraints=list(raw.get("non_negotiable_constraints", [])),
            created_at=str(raw.get("created_at", utc_now())),
            last_updated=str(raw.get("last_updated", utc_now())),
        )


@dataclass(frozen=True)
class IdentityChange:
    change_id: str
    target: str
    before: str
    after: str
    justification: str
    evidence: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "change_id": self.change_id,
            "target": self.target,
            "before": self.before,
            "after": self.after,
            "justification": self.justification,
            "evidence": self.evidence,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class NarrativeEvent:
    event_id: str
    event_type: str
    summary: str
    evidence: list[str] = field(default_factory=list)
    significance: str = "normal"
    timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "summary": self.summary,
            "evidence": self.evidence,
            "significance": self.significance,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "NarrativeEvent":
        return cls(
            event_id=str(raw["event_id"]),
            event_type=str(raw.get("event_type", "event")),
            summary=str(raw.get("summary", "")),
            evidence=list(raw.get("evidence", [])),
            significance=str(raw.get("significance", "normal")),
            timestamp=str(raw.get("timestamp", utc_now())),
        )
