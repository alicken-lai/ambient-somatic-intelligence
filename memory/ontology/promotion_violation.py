"""Promotion Violation records and logging.

Captures every blocked or flagged promotion attempt with full context
for governance review and system-wide audit trails.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PromotionViolation:
    """Record of a blocked or flagged promotion attempt."""

    violation_id: str
    source_level: str
    target_level: str
    reason: str
    confidence: float
    recurrence: int
    timestamp: str
    governance_reference: str
    blocked: bool
    source_file: str
    source_function: str
    entry_id: str = ""
    additional_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "violation_id": self.violation_id,
            "entry_id": self.entry_id,
            "source_level": self.source_level,
            "target_level": self.target_level,
            "reason": self.reason,
            "confidence": self.confidence,
            "recurrence": self.recurrence,
            "timestamp": self.timestamp,
            "governance_reference": self.governance_reference,
            "blocked": self.blocked,
            "source_file": self.source_file,
            "source_function": self.source_function,
            "additional_context": self.additional_context,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromotionViolation:
        return cls(
            violation_id=data["violation_id"],
            entry_id=data.get("entry_id", ""),
            source_level=data["source_level"],
            target_level=data["target_level"],
            reason=data["reason"],
            confidence=data["confidence"],
            recurrence=data["recurrence"],
            timestamp=data["timestamp"],
            governance_reference=data["governance_reference"],
            blocked=data["blocked"],
            source_file=data["source_file"],
            source_function=data["source_function"],
            additional_context=data.get("additional_context", {}),
        )


class ViolationLog:
    """Append-only log of all promotion violations.

    Persists violations to a JSONL file for long-term audit.
    Provides query capabilities for governance review.
    """

    def __init__(
        self,
        log_path: str | Path = "repair/audit/violations.jsonl",
    ) -> None:
        self._log_path = Path(log_path)
        self._violations: list[PromotionViolation] = []
        self._load()

    def record(self, violation: PromotionViolation) -> None:
        """Record a new violation and persist immediately."""
        self._violations.append(violation)
        self._append_to_file(violation)
        logger.warning(
            "PROMOTION VIOLATION [%s]: %s → %s blocked=%s reason=%r",
            violation.violation_id,
            violation.source_level,
            violation.target_level,
            violation.blocked,
            violation.reason,
        )

    def create_and_record(
        self,
        source_level: str,
        target_level: str,
        reason: str,
        confidence: float = 0.0,
        recurrence: int = 0,
        governance_reference: str = "",
        blocked: bool = True,
        source_file: str = "",
        source_function: str = "",
        entry_id: str = "",
        additional_context: dict[str, Any] | None = None,
    ) -> PromotionViolation:
        """Create a violation record and persist it in one call."""
        violation = PromotionViolation(
            violation_id=uuid.uuid4().hex[:12],
            entry_id=entry_id,
            source_level=source_level,
            target_level=target_level,
            reason=reason,
            confidence=confidence,
            recurrence=recurrence,
            timestamp=datetime.now(timezone.utc).isoformat(),
            governance_reference=governance_reference,
            blocked=blocked,
            source_file=source_file,
            source_function=source_function,
            additional_context=additional_context or {},
        )
        self.record(violation)
        return violation

    def get_all(self) -> list[PromotionViolation]:
        """Return all recorded violations."""
        return list(self._violations)

    def get_blocked(self) -> list[PromotionViolation]:
        """Return only blocked violations."""
        return [v for v in self._violations if v.blocked]

    def get_by_target_level(self, target_level: str) -> list[PromotionViolation]:
        """Return violations targeting a specific level."""
        return [v for v in self._violations if v.target_level == target_level]

    def count(self) -> int:
        """Total number of recorded violations."""
        return len(self._violations)

    def summary(self) -> dict[str, Any]:
        """Summary statistics for governance dashboards."""
        blocked = [v for v in self._violations if v.blocked]
        by_target: dict[str, int] = {}
        by_reason: dict[str, int] = {}
        for v in self._violations:
            by_target[v.target_level] = by_target.get(v.target_level, 0) + 1
            short_reason = v.reason.split(":")[0] if ":" in v.reason else v.reason
            by_reason[short_reason] = by_reason.get(short_reason, 0) + 1

        return {
            "total_violations": len(self._violations),
            "total_blocked": len(blocked),
            "by_target_level": by_target,
            "by_reason_category": by_reason,
        }

    def _append_to_file(self, violation: PromotionViolation) -> None:
        """Append a single violation to the JSONL log."""
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(violation.to_dict(), ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.error("Failed to persist violation: %s", exc)

    def _load(self) -> None:
        """Load existing violations from the JSONL log."""
        if not self._log_path.exists():
            return
        try:
            with self._log_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        self._violations.append(PromotionViolation.from_dict(data))
                    except (json.JSONDecodeError, KeyError) as exc:
                        logger.debug("Skipping malformed violation record: %s", exc)
        except OSError as exc:
            logger.error("Failed to load violation log: %s", exc)
