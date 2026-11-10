"""Data models for institutional reality alignment."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class RealityTarget:
    target_id: str
    target_type: str
    statement: str
    confidence: float
    trust_score: float = 0.0
    verification_success: float = 0.0
    historical_quality: float = 0.0
    outcome_quality: float = 0.0
    sources: list[str] = field(default_factory=list)
    internal_sources: list[str] = field(default_factory=list)
    external_sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "target_type": self.target_type,
            "statement": self.statement,
            "confidence": self.confidence,
            "trust_score": self.trust_score,
            "verification_success": self.verification_success,
            "historical_quality": self.historical_quality,
            "outcome_quality": self.outcome_quality,
            "sources": self.sources,
            "internal_sources": self.internal_sources,
            "external_sources": self.external_sources,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RealityTarget":
        return cls(
            target_id=str(raw["target_id"]),
            target_type=str(raw["target_type"]),
            statement=str(raw["statement"]),
            confidence=float(raw.get("confidence", 0.0)),
            trust_score=float(raw.get("trust_score", 0.0)),
            verification_success=float(raw.get("verification_success", 0.0)),
            historical_quality=float(raw.get("historical_quality", 0.0)),
            outcome_quality=float(raw.get("outcome_quality", 0.0)),
            sources=list(raw.get("sources", [])),
            internal_sources=list(raw.get("internal_sources", [])),
            external_sources=list(raw.get("external_sources", [])),
        )


@dataclass(frozen=True)
class RealityObservation:
    observation_id: str
    target_id: str
    source_type: str
    agreement: float
    outcome_quality: float
    verification_success: bool
    notes: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "target_id": self.target_id,
            "source_type": self.source_type,
            "agreement": self.agreement,
            "outcome_quality": self.outcome_quality,
            "verification_success": self.verification_success,
            "notes": self.notes,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RealityObservation":
        return cls(
            observation_id=str(raw["observation_id"]),
            target_id=str(raw["target_id"]),
            source_type=str(raw.get("source_type", "internal")),
            agreement=float(raw.get("agreement", 0.0)),
            outcome_quality=float(raw.get("outcome_quality", 0.0)),
            verification_success=bool(raw.get("verification_success", False)),
            notes=list(raw.get("notes", [])),
            timestamp=str(raw.get("timestamp", utc_now())),
        )


@dataclass(frozen=True)
class ChallengeResult:
    challenge_id: str
    target_id: str
    target_type: str
    prior_confidence: float
    reality_score: float
    passed: bool
    reason: str
    challenged_because: str
    timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "challenge_id": self.challenge_id,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "prior_confidence": self.prior_confidence,
            "reality_score": self.reality_score,
            "passed": self.passed,
            "reason": self.reason,
            "challenged_because": self.challenged_because,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class FitnessResult:
    target_id: str
    target_type: str
    fitness_score: float
    trend: str
    reasoning: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "target_type": self.target_type,
            "fitness_score": self.fitness_score,
            "trend": self.trend,
            "reasoning": self.reasoning,
        }


@dataclass(frozen=True)
class Belief:
    belief_id: str
    statement: str
    confidence: float
    reality_score: float
    challenge_count: int = 0
    status: str = "active"
    source_target_id: str | None = None
    last_updated: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "belief_id": self.belief_id,
            "statement": self.statement,
            "confidence": self.confidence,
            "reality_score": self.reality_score,
            "challenge_count": self.challenge_count,
            "status": self.status,
            "source_target_id": self.source_target_id,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Belief":
        return cls(
            belief_id=str(raw["belief_id"]),
            statement=str(raw["statement"]),
            confidence=float(raw.get("confidence", 0.0)),
            reality_score=float(raw.get("reality_score", 0.0)),
            challenge_count=int(raw.get("challenge_count", 0)),
            status=str(raw.get("status", "active")),
            source_target_id=raw.get("source_target_id"),
            last_updated=str(raw.get("last_updated", utc_now())),
        )


@dataclass(frozen=True)
class ValidationSource:
    source_id: str
    name: str
    source_type: str
    advisory_only: bool = True
    capabilities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "source_type": self.source_type,
            "advisory_only": self.advisory_only,
            "capabilities": self.capabilities,
        }


@dataclass(frozen=True)
class ValidationOutcome:
    outcome_id: str
    source_id: str
    target_id: str
    agreement: float
    outcome_quality: float
    notes: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome_id": self.outcome_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "agreement": self.agreement,
            "outcome_quality": self.outcome_quality,
            "notes": self.notes,
            "timestamp": self.timestamp,
        }
