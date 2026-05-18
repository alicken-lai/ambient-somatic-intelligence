"""
Daily Health Checker — Computes daily telemetry health metrics.

Designed to run at the end of each day during maturation.
Produces a structured report with cadence compliance, gap analysis,
duplicate detection, clock drift assessment, and replay compatibility.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


THRESHOLDS = {
    "cadence_compliance": 0.95,
    "missing_interval_max": 0.05,
    "duplicate_rate_max": 0.01,
    "clock_drift_max_seconds": 5.0,
}

EXPECTED_SOURCES = [
    "dmn.tick",
    "actions.log",
    "checksums.log",
    "governance.decisions",
    "governance.incidents",
    "agent.decisions",
    "health.snapshot",
]

EXPECTED_CADENCE_SECONDS = {
    "dmn.tick": 300,
    "actions.log": 300,
    "checksums.log": 300,
    "governance.decisions": 300,
    "governance.incidents": 300,
    "agent.decisions": 300,
    "health.snapshot": 300,
}

SECONDS_PER_DAY = 86400


@dataclass
class DailyHealthReport:
    """Structured daily health report."""
    day: str
    date: str
    status: str
    metrics: dict[str, Any] = field(default_factory=dict)
    thresholds_met: bool = False
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "day": self.day,
            "date": self.date,
            "status": self.status,
            "metrics": self.metrics,
            "thresholds_met": self.thresholds_met,
            "issues": self.issues,
        }


class DailyHealthChecker:
    """Computes daily telemetry health metrics.

    Designed to run at end of each day during maturation.
    Accepts a day capture dict (the day_XX.json format) and
    produces a DailyHealthReport.
    """

    def __init__(
        self,
        thresholds: dict[str, float] | None = None,
        expected_sources: list[str] | None = None,
    ):
        self._thresholds = thresholds or dict(THRESHOLDS)
        self._expected_sources = expected_sources or list(EXPECTED_SOURCES)

    def check(self, day_data: dict[str, Any]) -> DailyHealthReport:
        """Run all health checks on a day capture dict."""
        day = day_data.get("day", "unknown")
        date = day_data.get("date", "unknown")
        status = day_data.get("status", "UNKNOWN")

        if status == "AWAITING_CAPTURE":
            return DailyHealthReport(
                day=day,
                date=date,
                status="AWAITING_DATA",
                metrics={},
                thresholds_met=False,
                issues=["No data available for this day"],
            )

        records = day_data.get("records", [])
        sources_map = day_data.get("sources", {})
        capture_window = day_data.get("capture_window", {})

        cadence_compliance = self._compute_cadence_compliance(records, capture_window)
        missing_rate = self._compute_missing_interval_rate(records, capture_window)
        duplicate_rate = self._compute_duplicate_rate(records)
        max_drift = self._compute_max_clock_drift(records)
        corruption_count = self._compute_corruption_count(records)
        silent_sources = self._detect_silent_sources(sources_map)
        replay_compat = self._compute_replay_compatibility(
            cadence_compliance, missing_rate, duplicate_rate, max_drift
        )

        metrics = {
            "cadence_compliance": round(cadence_compliance, 4),
            "missing_interval_rate": round(missing_rate, 4),
            "duplicate_rate": round(duplicate_rate, 4),
            "max_clock_drift_seconds": round(max_drift, 3),
            "corruption_count": corruption_count,
            "silent_sources": silent_sources,
            "replay_compatibility": round(replay_compat, 4),
        }

        issues = []
        thresholds_met = True

        if cadence_compliance < self._thresholds["cadence_compliance"]:
            issues.append(
                f"Cadence compliance {cadence_compliance:.2%} below "
                f"threshold {self._thresholds['cadence_compliance']:.0%}"
            )
            thresholds_met = False

        if missing_rate > self._thresholds["missing_interval_max"]:
            issues.append(
                f"Missing interval rate {missing_rate:.2%} above "
                f"threshold {self._thresholds['missing_interval_max']:.0%}"
            )
            thresholds_met = False

        if duplicate_rate > self._thresholds["duplicate_rate_max"]:
            issues.append(
                f"Duplicate rate {duplicate_rate:.4f} above "
                f"threshold {self._thresholds['duplicate_rate_max']}"
            )
            thresholds_met = False

        if max_drift > self._thresholds["clock_drift_max_seconds"]:
            issues.append(
                f"Clock drift {max_drift:.3f}s above "
                f"threshold {self._thresholds['clock_drift_max_seconds']}s"
            )
            thresholds_met = False

        if corruption_count > 0:
            issues.append(f"{corruption_count} corrupted/malformed records detected")

        if silent_sources:
            issues.append(f"Silent sources: {', '.join(silent_sources)}")

        if status == "PARTIAL":
            issues.append("Partial day — not all 24 hours covered")

        return DailyHealthReport(
            day=day,
            date=date,
            status="COMPLETE" if status == "CAPTURED" else status,
            metrics=metrics,
            thresholds_met=thresholds_met,
            issues=issues,
        )

    def _compute_cadence_compliance(
        self,
        records: list[dict],
        capture_window: dict,
    ) -> float:
        """Fraction of expected intervals that received at least one sample."""
        if not records:
            return 0.0

        source_timestamps: dict[str, list[float]] = defaultdict(list)
        for rec in records:
            src = rec.get("source", "unknown")
            ts_unix = rec.get("timestamp_unix", 0.0)
            if ts_unix > 0:
                source_timestamps[src].append(ts_unix)

        if not source_timestamps:
            return 0.0

        total_intervals = 0
        compliant_intervals = 0

        for src, timestamps in source_timestamps.items():
            if len(timestamps) < 2:
                continue
            timestamps.sort()
            cadence = EXPECTED_CADENCE_SECONDS.get(src, 300)
            max_acceptable = cadence * 1.5

            for i in range(1, len(timestamps)):
                gap = timestamps[i] - timestamps[i - 1]
                total_intervals += 1
                if gap <= max_acceptable:
                    compliant_intervals += 1

        if total_intervals == 0:
            return 1.0
        return compliant_intervals / total_intervals

    def _compute_missing_interval_rate(
        self,
        records: list[dict],
        capture_window: dict,
    ) -> float:
        """Fraction of expected 5-minute intervals with zero records."""
        start_str = capture_window.get("start", "")
        end_str = capture_window.get("end", "")
        if not start_str or not end_str:
            return 1.0

        try:
            start_ts = datetime.fromisoformat(start_str).timestamp()
            end_ts = datetime.fromisoformat(end_str).timestamp()
        except (ValueError, TypeError):
            return 1.0

        duration = end_ts - start_ts
        if duration <= 0:
            return 1.0

        interval = 300
        expected_intervals = max(1, int(duration / interval))

        occupied = set()
        for rec in records:
            ts_unix = rec.get("timestamp_unix", 0.0)
            if ts_unix > 0:
                bucket = int((ts_unix - start_ts) / interval)
                occupied.add(bucket)

        missing = expected_intervals - len(occupied)
        return max(0.0, missing / expected_intervals)

    def _compute_duplicate_rate(self, records: list[dict]) -> float:
        """Detect near-duplicate records by source+timestamp proximity."""
        if not records:
            return 0.0

        source_times: dict[str, list[float]] = defaultdict(list)
        for rec in records:
            src = rec.get("source", "unknown")
            ts_unix = rec.get("timestamp_unix", 0.0)
            if ts_unix > 0:
                source_times[src].append(ts_unix)

        total = len(records)
        duplicates = 0
        near_dup_window = 10.0

        for src, times in source_times.items():
            times.sort()
            for i in range(1, len(times)):
                if (times[i] - times[i - 1]) < near_dup_window:
                    duplicates += 1

        return duplicates / total if total > 0 else 0.0

    def _compute_max_clock_drift(self, records: list[dict]) -> float:
        """Estimate clock drift from timestamp consistency."""
        if not records:
            return 0.0

        drifts = []
        for rec in records:
            ts_str = rec.get("timestamp", "")
            ts_unix = rec.get("timestamp_unix", 0.0)
            if ts_str and ts_unix > 0:
                try:
                    parsed = datetime.fromisoformat(ts_str).timestamp()
                    drift = abs(parsed - ts_unix)
                    if drift > 0.001:
                        drifts.append(drift)
                except (ValueError, TypeError):
                    pass

        return max(drifts) if drifts else 0.0

    def _compute_corruption_count(self, records: list[dict]) -> int:
        """Count records missing required fields."""
        corruption = 0
        for rec in records:
            if not rec.get("source"):
                corruption += 1
            elif not rec.get("timestamp"):
                corruption += 1
            elif rec.get("timestamp_unix", 0.0) <= 0:
                corruption += 1
        return corruption

    def _detect_silent_sources(self, sources_map: dict) -> list[str]:
        """Return expected sources with zero records."""
        silent = []
        for src in self._expected_sources:
            if sources_map.get(src, 0) == 0:
                silent.append(src)
        return silent

    def _compute_replay_compatibility(
        self,
        cadence_compliance: float,
        missing_rate: float,
        duplicate_rate: float,
        max_drift: float,
    ) -> float:
        """Composite score reflecting how suitable data is for replay."""
        cadence_score = cadence_compliance
        gap_score = 1.0 - missing_rate
        dup_score = 1.0 - min(1.0, duplicate_rate * 10)
        drift_score = max(0.0, 1.0 - (max_drift / 30.0))

        return (
            cadence_score * 0.35
            + gap_score * 0.35
            + dup_score * 0.15
            + drift_score * 0.15
        )

    def check_file(self, day_file_path: str | Path) -> DailyHealthReport:
        """Load a day file and run health checks."""
        path = Path(day_file_path)
        with open(path) as f:
            data = json.load(f)
        return self.check(data)

    def generate_report_file(
        self,
        day_data: dict[str, Any],
        output_path: str | Path,
    ) -> DailyHealthReport:
        """Run checks and write the report to disk."""
        report = self.check(day_data)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        return report
