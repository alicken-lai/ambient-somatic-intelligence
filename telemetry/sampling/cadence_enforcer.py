"""
Cadence Enforcer — Monitors sampling sources for cadence compliance.

Tracks actual sampling intervals versus declared cadence, detects violations
and silent sources, computes per-source compliance scores, and generates
compliance reports compatible with the existing health-scoring pipeline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from telemetry.sampling.sampling_policy import SamplingPolicy

logger = logging.getLogger(__name__)


@dataclass
class CadenceViolation:
    """Record of a single cadence violation."""
    source_name: str
    expected_interval_seconds: int
    actual_interval_seconds: float
    timestamp: str
    violation_type: str  # "late" | "silent" | "gap"
    severity: str        # "minor" | "major" | "critical"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_name": self.source_name,
            "expected_interval_seconds": self.expected_interval_seconds,
            "actual_interval_seconds": round(self.actual_interval_seconds, 2),
            "timestamp": self.timestamp,
            "violation_type": self.violation_type,
            "severity": self.severity,
        }


@dataclass
class SourceComplianceRecord:
    """Compliance tracking for a single source."""
    source_name: str
    policy: SamplingPolicy
    total_intervals: int = 0
    compliant_intervals: int = 0
    violations: list[CadenceViolation] = field(default_factory=list)
    last_sample_timestamp: Optional[float] = None
    max_observed_gap_seconds: float = 0.0
    min_observed_gap_seconds: float = float("inf")
    sum_gap_seconds: float = 0.0

    @property
    def compliance_score(self) -> float:
        if self.total_intervals == 0:
            return 1.0
        return self.compliant_intervals / self.total_intervals

    @property
    def avg_gap_seconds(self) -> float:
        if self.total_intervals == 0:
            return 0.0
        return self.sum_gap_seconds / self.total_intervals

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_name": self.source_name,
            "desired_cadence_seconds": self.policy.desired_cadence_seconds,
            "total_intervals": self.total_intervals,
            "compliant_intervals": self.compliant_intervals,
            "compliance_score": round(self.compliance_score, 4),
            "violation_count": self.violation_count,
            "max_observed_gap_seconds": round(self.max_observed_gap_seconds, 2),
            "min_observed_gap_seconds": (
                round(self.min_observed_gap_seconds, 2)
                if self.min_observed_gap_seconds != float("inf")
                else None
            ),
            "avg_gap_seconds": round(self.avg_gap_seconds, 2),
            "recent_violations": [v.to_dict() for v in self.violations[-10:]],
        }


# Violation-severity thresholds: ratio of actual/expected interval
_MINOR_THRESHOLD = 1.5
_MAJOR_THRESHOLD = 3.0
_CRITICAL_THRESHOLD = 10.0

# A source silent for this many multiples of its cadence is flagged
_SILENT_MULTIPLIER = 5.0

_MAX_VIOLATIONS_PER_SOURCE = 500


class CadenceEnforcer:
    """Monitors all registered sources and ensures they meet their
    declared cadence.  Flags violations and generates reports.

    Parameters
    ----------
    clock_fn:
        Callable returning current time as float.  Override for replay.
    silent_threshold_multiplier:
        A source is considered "silent" if no sample has arrived for
        ``cadence * multiplier`` seconds.
    """

    def __init__(
        self,
        clock_fn=None,
        silent_threshold_multiplier: float = _SILENT_MULTIPLIER,
    ):
        import time as _time
        self._clock = clock_fn or _time.time
        self._silent_multiplier = silent_threshold_multiplier
        self._records: dict[str, SourceComplianceRecord] = {}

    # ── Registration ──────────────────────────────────────────────────

    def register(self, policy: SamplingPolicy) -> None:
        """Start tracking compliance for a source."""
        if policy.source_name not in self._records:
            self._records[policy.source_name] = SourceComplianceRecord(
                source_name=policy.source_name,
                policy=policy,
            )

    def unregister(self, source_name: str) -> bool:
        return self._records.pop(source_name, None) is not None

    # ── Event recording ───────────────────────────────────────────────

    def record_sample(self, source_name: str, timestamp: float | None = None) -> Optional[CadenceViolation]:
        """Record that a sample was collected from ``source_name``.

        Returns a CadenceViolation if the interval exceeded the policy,
        or None if compliant.
        """
        rec = self._records.get(source_name)
        if rec is None:
            logger.warning("record_sample called for unregistered source '%s'", source_name)
            return None

        now = timestamp if timestamp is not None else self._clock()
        violation: Optional[CadenceViolation] = None

        if rec.last_sample_timestamp is not None:
            gap = now - rec.last_sample_timestamp
            rec.total_intervals += 1
            rec.sum_gap_seconds += gap
            rec.max_observed_gap_seconds = max(rec.max_observed_gap_seconds, gap)
            rec.min_observed_gap_seconds = min(rec.min_observed_gap_seconds, gap)

            max_acceptable = rec.policy.max_acceptable_interval_seconds
            if gap <= max_acceptable:
                rec.compliant_intervals += 1
            else:
                violation = self._create_violation(rec, gap, now)
                rec.violations.append(violation)
                if len(rec.violations) > _MAX_VIOLATIONS_PER_SOURCE:
                    rec.violations = rec.violations[-_MAX_VIOLATIONS_PER_SOURCE:]
                logger.warning(
                    "Cadence violation for '%s': gap=%.1fs expected<=%ds severity=%s",
                    source_name,
                    gap,
                    max_acceptable,
                    violation.severity,
                )

        rec.last_sample_timestamp = now
        return violation

    # ── Silent-source detection ───────────────────────────────────────

    def detect_silent_sources(self) -> list[CadenceViolation]:
        """Check all sources for silence (no sample in a long time)."""
        now = self._clock()
        violations: list[CadenceViolation] = []

        for rec in self._records.values():
            if rec.last_sample_timestamp is None:
                continue
            silence_threshold = rec.policy.desired_cadence_seconds * self._silent_multiplier
            gap = now - rec.last_sample_timestamp
            if gap > silence_threshold:
                v = CadenceViolation(
                    source_name=rec.source_name,
                    expected_interval_seconds=rec.policy.desired_cadence_seconds,
                    actual_interval_seconds=gap,
                    timestamp=datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
                    violation_type="silent",
                    severity="critical",
                )
                violations.append(v)
                rec.violations.append(v)
                if len(rec.violations) > _MAX_VIOLATIONS_PER_SOURCE:
                    rec.violations = rec.violations[-_MAX_VIOLATIONS_PER_SOURCE:]
                logger.error(
                    "Silent source detected: '%s' last seen %.0fs ago (threshold=%.0fs)",
                    rec.source_name,
                    gap,
                    silence_threshold,
                )

        return violations

    # ── Reports ───────────────────────────────────────────────────────

    def compliance_report(self) -> dict[str, Any]:
        """Generate a full cadence compliance report."""
        now_iso = datetime.fromtimestamp(self._clock(), tz=timezone.utc).isoformat()
        sources = {name: rec.to_dict() for name, rec in self._records.items()}
        scores = [rec.compliance_score for rec in self._records.values()]
        overall = sum(scores) / len(scores) if scores else 1.0

        total_violations = sum(rec.violation_count for rec in self._records.values())

        return {
            "generated_at": now_iso,
            "overall_compliance_score": round(overall, 4),
            "sources_tracked": len(self._records),
            "total_violations": total_violations,
            "sources": sources,
        }

    def source_report(self, source_name: str) -> dict[str, Any] | None:
        rec = self._records.get(source_name)
        return rec.to_dict() if rec else None

    def compliance_score(self, source_name: str) -> float | None:
        rec = self._records.get(source_name)
        return rec.compliance_score if rec else None

    def overall_compliance_score(self) -> float:
        scores = [rec.compliance_score for rec in self._records.values()]
        return sum(scores) / len(scores) if scores else 1.0

    def all_violations(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return the most recent violations across all sources."""
        all_v: list[CadenceViolation] = []
        for rec in self._records.values():
            all_v.extend(rec.violations)
        all_v.sort(key=lambda v: v.timestamp, reverse=True)
        return [v.to_dict() for v in all_v[:limit]]

    # ── Internals ─────────────────────────────────────────────────────

    @staticmethod
    def _create_violation(
        rec: SourceComplianceRecord,
        gap: float,
        now: float,
    ) -> CadenceViolation:
        ratio = gap / rec.policy.desired_cadence_seconds
        if ratio >= _CRITICAL_THRESHOLD:
            severity = "critical"
        elif ratio >= _MAJOR_THRESHOLD:
            severity = "major"
        else:
            severity = "minor"

        vtype = "gap" if gap > rec.policy.desired_cadence_seconds * 3 else "late"

        return CadenceViolation(
            source_name=rec.source_name,
            expected_interval_seconds=rec.policy.desired_cadence_seconds,
            actual_interval_seconds=gap,
            timestamp=datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
            violation_type=vtype,
            severity=severity,
        )
