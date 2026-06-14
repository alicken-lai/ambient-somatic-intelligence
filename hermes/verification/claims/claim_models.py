"""Claim data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


CLAIM_TYPES = {"fact", "prediction", "recommendation", "assumption", "policy", "architecture", "security", "governance"}


@dataclass(frozen=True)
class Claim:
    claim_id: str
    claim_text: str
    source: str
    claim_type: str
    risk_level: str
    verification_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "source": self.source,
            "claim_type": self.claim_type,
            "risk_level": self.risk_level,
            "verification_required": self.verification_required,
        }


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    status: str = "pending"
    evidence: list[str] = field(default_factory=list)
    last_checked: str | None = None
    verification_count: int = 0
    challenge_history: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "status": self.status,
            "evidence": self.evidence,
            "last_checked": self.last_checked,
            "verification_count": self.verification_count,
            "challenge_history": self.challenge_history,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ClaimRecord":
        return cls(
            claim_id=str(raw["claim_id"]),
            status=str(raw.get("status", "pending")),
            evidence=list(raw.get("evidence", [])),
            last_checked=raw.get("last_checked"),
            verification_count=int(raw.get("verification_count", 0)),
            challenge_history=list(raw.get("challenge_history", [])),
        )
