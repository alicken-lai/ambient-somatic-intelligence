"""
Timestamp Validator — Detects ordering anomalies, duplicates, and timezone issues.

Validates a stream of TelemetryRecords for:
  - Out-of-order timestamps
  - Duplicate timestamps (same source, same time)
  - Unreasonable time jumps (forward or backward)
  - Timezone consistency
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from telemetry.core.telemetry_schema import TelemetryRecord


@dataclass
class TimestampIssue:
    """A single timestamp validation issue."""
    issue_type: str  # "out_of_order", "duplicate", "time_jump", "timezone_mismatch", "missing"
    record_id: str
    source: str
    timestamp: str
    details: str
    severity: str = "warning"  # "info", "warning", "error"

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_type": self.issue_type,
            "record_id": self.record_id,
            "source": self.source,
            "timestamp": self.timestamp,
            "details": self.details,
            "severity": self.severity,
        }


@dataclass
class ValidationResult:
    """Aggregated validation results."""
    total_records: int = 0
    valid_records: int = 0
    issues: list[TimestampIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    def to_dict(self) -> dict[str, Any]:
        issue_summary: dict[str, int] = {}
        for issue in self.issues:
            issue_summary[issue.issue_type] = issue_summary.get(issue.issue_type, 0) + 1

        return {
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "issue_count": self.issue_count,
            "is_valid": self.is_valid,
            "issue_summary": issue_summary,
            "issues": [i.to_dict() for i in self.issues[:100]],
        }


class TimestampValidator:
    """Validates timestamp consistency across a stream of TelemetryRecords."""

    def __init__(
        self,
        max_forward_jump_seconds: float = 86400 * 7,
        max_backward_jump_seconds: float = 60,
    ):
        self._max_forward = max_forward_jump_seconds
        self._max_backward = max_backward_jump_seconds

    def validate(self, records: list[TelemetryRecord]) -> ValidationResult:
        """Validate a list of records for timestamp consistency."""
        result = ValidationResult(total_records=len(records))
        if not records:
            return result

        last_ts_by_source: dict[str, float] = {}
        seen_ts_by_source: dict[str, set[float]] = {}

        for record in records:
            ts = record.timestamp_unix
            src = record.source
            valid = True

            if not record.timestamp or ts <= 0:
                result.issues.append(TimestampIssue(
                    issue_type="missing",
                    record_id=record.record_id,
                    source=src,
                    timestamp=record.timestamp,
                    details="Missing or zero timestamp",
                    severity="error",
                ))
                valid = False
                continue

            if not record.timestamp.endswith("+00:00") and "Z" not in record.timestamp:
                if "+" not in record.timestamp and "-" not in record.timestamp[19:]:
                    result.issues.append(TimestampIssue(
                        issue_type="timezone_mismatch",
                        record_id=record.record_id,
                        source=src,
                        timestamp=record.timestamp,
                        details="Timestamp lacks timezone info — may not be UTC",
                        severity="warning",
                    ))

            if src in last_ts_by_source:
                prev_ts = last_ts_by_source[src]
                delta = ts - prev_ts

                if delta < -self._max_backward:
                    result.issues.append(TimestampIssue(
                        issue_type="out_of_order",
                        record_id=record.record_id,
                        source=src,
                        timestamp=record.timestamp,
                        details=f"Timestamp is {abs(delta):.1f}s before previous record from same source",
                        severity="error",
                    ))
                    valid = False

                if delta > self._max_forward:
                    result.issues.append(TimestampIssue(
                        issue_type="time_jump",
                        record_id=record.record_id,
                        source=src,
                        timestamp=record.timestamp,
                        details=f"Forward jump of {delta / 3600:.1f}h from previous record",
                        severity="warning",
                    ))

            if src not in seen_ts_by_source:
                seen_ts_by_source[src] = set()
            ts_key = round(ts, 3)
            if ts_key in seen_ts_by_source[src]:
                result.issues.append(TimestampIssue(
                    issue_type="duplicate",
                    record_id=record.record_id,
                    source=src,
                    timestamp=record.timestamp,
                    details="Duplicate timestamp within same source (within 1ms)",
                    severity="info",
                ))
            seen_ts_by_source[src].add(ts_key)

            last_ts_by_source[src] = ts
            if valid:
                result.valid_records += 1

        return result
