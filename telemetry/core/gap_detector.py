"""
Gap Detector — Identifies and classifies telemetry gaps.

Accepts a stream of TelemetryRecords and detects gaps larger than
the expected cadence. Classifies gaps by severity, identifies patterns
(e.g., recurring gaps at the same time of day), and generates reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from telemetry.core.telemetry_schema import TelemetryRecord


class GapSeverity(str, Enum):
    SHORT = "short"        # < 10 minutes
    MEDIUM = "medium"      # 10-60 minutes
    LONG = "long"          # 1-8 hours
    CRITICAL = "critical"  # > 8 hours


def _classify_gap(duration_seconds: float) -> GapSeverity:
    if duration_seconds < 600:
        return GapSeverity.SHORT
    if duration_seconds < 3600:
        return GapSeverity.MEDIUM
    if duration_seconds < 28800:
        return GapSeverity.LONG
    return GapSeverity.CRITICAL


@dataclass
class Gap:
    """A detected telemetry gap."""
    gap_id: str
    source: str
    start_time: str
    start_unix: float
    end_time: str
    end_unix: float
    duration_seconds: float
    severity: str
    records_before: int
    records_after: int
    expected_records: int = 0

    @property
    def duration_human(self) -> str:
        s = self.duration_seconds
        if s < 60:
            return f"{s:.0f}s"
        if s < 3600:
            return f"{s / 60:.0f}m {s % 60:.0f}s"
        hours = int(s // 3600)
        mins = int((s % 3600) // 60)
        return f"{hours}h {mins}m"

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "source": self.source,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": round(self.duration_seconds, 2),
            "duration_human": self.duration_human,
            "severity": self.severity,
            "records_before": self.records_before,
            "records_after": self.records_after,
            "expected_records": self.expected_records,
        }


@dataclass
class GapReport:
    """Aggregated gap detection results."""
    source: str
    total_records: int
    total_gaps: int
    gaps: list[Gap] = field(default_factory=list)
    coverage_ratio: float = 1.0
    total_gap_seconds: float = 0.0
    longest_gap_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        severity_counts = {}
        for gap in self.gaps:
            severity_counts[gap.severity] = severity_counts.get(gap.severity, 0) + 1

        return {
            "source": self.source,
            "total_records": self.total_records,
            "total_gaps": self.total_gaps,
            "severity_counts": severity_counts,
            "coverage_ratio": round(self.coverage_ratio, 4),
            "total_gap_seconds": round(self.total_gap_seconds, 2),
            "total_gap_human": Gap(
                gap_id="", source="", start_time="", start_unix=0,
                end_time="", end_unix=0, duration_seconds=self.total_gap_seconds,
                severity="", records_before=0, records_after=0,
            ).duration_human,
            "longest_gap_seconds": round(self.longest_gap_seconds, 2),
            "gaps": [g.to_dict() for g in self.gaps],
        }


class GapDetector:
    """Detects and classifies gaps in telemetry streams."""

    def __init__(self, default_expected_interval_seconds: float = 60.0):
        self._default_interval = default_expected_interval_seconds
        self._source_intervals: dict[str, float] = {}

    def set_expected_interval(self, source: str, interval_seconds: float) -> None:
        """Set the expected cadence for a specific source."""
        self._source_intervals[source] = interval_seconds

    def detect_gaps(
        self,
        records: list[TelemetryRecord],
        source_filter: str | None = None,
        min_gap_multiplier: float = 3.0,
    ) -> GapReport:
        """Detect gaps in a sorted list of TelemetryRecords.

        A gap is detected when the interval between consecutive records
        exceeds ``expected_interval * min_gap_multiplier``.
        """
        filtered = records
        if source_filter:
            filtered = [r for r in records if r.source == source_filter or source_filter in r.source]

        filtered.sort(key=lambda r: r.timestamp_unix)

        source_name = source_filter or "all"
        if not filtered:
            return GapReport(source=source_name, total_records=0, total_gaps=0)

        expected = self._source_intervals.get(source_name, self._default_interval)
        threshold = expected * min_gap_multiplier

        gaps: list[Gap] = []
        total_gap_seconds = 0.0
        longest = 0.0
        gap_counter = 0

        for i in range(1, len(filtered)):
            prev = filtered[i - 1]
            curr = filtered[i]
            delta = curr.timestamp_unix - prev.timestamp_unix

            if delta > threshold:
                gap_counter += 1
                severity = _classify_gap(delta)
                expected_records = int(delta / expected) if expected > 0 else 0

                gap = Gap(
                    gap_id=f"GAP-{source_name}-{gap_counter:03d}",
                    source=source_name,
                    start_time=prev.timestamp,
                    start_unix=prev.timestamp_unix,
                    end_time=curr.timestamp,
                    end_unix=curr.timestamp_unix,
                    duration_seconds=delta,
                    severity=severity.value,
                    records_before=i,
                    records_after=len(filtered) - i,
                    expected_records=expected_records,
                )
                gaps.append(gap)
                total_gap_seconds += delta
                longest = max(longest, delta)

        total_span = filtered[-1].timestamp_unix - filtered[0].timestamp_unix
        coverage = 1.0 - (total_gap_seconds / total_span) if total_span > 0 else 1.0

        return GapReport(
            source=source_name,
            total_records=len(filtered),
            total_gaps=len(gaps),
            gaps=gaps,
            coverage_ratio=max(0.0, coverage),
            total_gap_seconds=total_gap_seconds,
            longest_gap_seconds=longest,
        )

    def detect_gaps_all_sources(
        self,
        records: list[TelemetryRecord],
        min_gap_multiplier: float = 3.0,
    ) -> dict[str, GapReport]:
        """Detect gaps grouped by source."""
        by_source: dict[str, list[TelemetryRecord]] = {}
        for r in records:
            by_source.setdefault(r.source, []).append(r)

        reports = {}
        for source, source_records in by_source.items():
            source_records.sort(key=lambda r: r.timestamp_unix)
            reports[source] = self.detect_gaps(source_records, source_filter=source, min_gap_multiplier=min_gap_multiplier)

        return reports

    def find_gap_patterns(self, gaps: list[Gap]) -> list[dict[str, Any]]:
        """Identify recurring patterns in gaps (same time of day, same duration, etc.)."""
        if not gaps:
            return []

        patterns: list[dict[str, Any]] = []

        hour_counts: dict[int, int] = {}
        for gap in gaps:
            if gap.start_unix > 0:
                dt = datetime.fromtimestamp(gap.start_unix, tz=timezone.utc)
                hour_counts[dt.hour] = hour_counts.get(dt.hour, 0) + 1

        for hour, count in sorted(hour_counts.items(), key=lambda x: -x[1]):
            if count >= 2:
                patterns.append({
                    "type": "recurring_hour",
                    "hour_utc": hour,
                    "count": count,
                    "description": f"Gaps frequently start at hour {hour:02d} UTC ({count} occurrences)",
                })

        duration_bands = {"short": 0, "medium": 0, "long": 0, "critical": 0}
        for gap in gaps:
            duration_bands[gap.severity] = duration_bands.get(gap.severity, 0) + 1

        dominant = max(duration_bands, key=lambda k: duration_bands[k])
        if duration_bands[dominant] > len(gaps) * 0.5:
            patterns.append({
                "type": "dominant_severity",
                "severity": dominant,
                "ratio": round(duration_bands[dominant] / len(gaps), 2),
                "description": f"Most gaps ({duration_bands[dominant]}/{len(gaps)}) are {dominant} severity",
            })

        return patterns
