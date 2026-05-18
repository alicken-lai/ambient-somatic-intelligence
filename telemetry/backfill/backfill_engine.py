"""
Backfill Engine — Orchestrates historical data normalization, gap detection, and filling.

Loads all historical data, normalizes through TelemetryNormalizer,
detects gaps using GapDetector, and fills using InterpolationEngine.
Produces dense replay windows around known incidents with full
confidence tagging.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from telemetry.core.telemetry_schema import TelemetryRecord, DataOrigin
from telemetry.core.telemetry_normalizer import TelemetryNormalizer
from telemetry.core.gap_detector import GapDetector, GapReport
from telemetry.core.timestamp_validator import TimestampValidator
from telemetry.backfill.interpolation_engine import InterpolationEngine
from telemetry.backfill.confidence_tagger import ConfidenceTagger, ConfidenceReport

logger = logging.getLogger(__name__)

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))


class BackfillEngine:
    """Orchestrates the full backfill pipeline."""

    def __init__(self, root: Path | None = None):
        self._root = root or AMBIENT_ROOT
        self._normalizer = TelemetryNormalizer()
        self._gap_detector = GapDetector(default_expected_interval_seconds=60.0)
        self._validator = TimestampValidator()
        self._interpolator = InterpolationEngine(max_interpolation_seconds=3600.0)
        self._tagger = ConfidenceTagger()

        self._all_records: list[TelemetryRecord] = []
        self._backfilled_records: list[TelemetryRecord] = []
        self._gap_reports: dict[str, GapReport] = {}

    def load_historical_data(self) -> int:
        """Load and normalize all historical data sources."""
        total = 0

        total += self._load_dmn()
        total += self._load_actions()
        total += self._load_health_scores()
        total += self._load_incidents()
        total += self._load_governance()
        total += self._load_archived_scratchpad()

        self._all_records.sort(key=lambda r: r.timestamp_unix)
        logger.info("Loaded %d total records across all sources", total)
        return total

    def detect_all_gaps(self) -> dict[str, GapReport]:
        """Detect gaps across all loaded sources."""
        self._gap_reports = self._gap_detector.detect_gaps_all_sources(self._all_records)
        return self._gap_reports

    def create_dense_window(
        self,
        center_time: str,
        window_before_minutes: int = 60,
        window_after_minutes: int = 10,
        target_interval_seconds: float = 60.0,
    ) -> list[TelemetryRecord]:
        """Create a dense replay window around a specific time point.

        Fills gaps within the window using interpolation where possible,
        marks UNKNOWN where not.
        """
        from telemetry.core.telemetry_normalizer import parse_timestamp
        _, center_unix = parse_timestamp(center_time)

        window_start = center_unix - (window_before_minutes * 60)
        window_end = center_unix + (window_after_minutes * 60)

        window_records = [
            r for r in self._all_records
            if window_start <= r.timestamp_unix <= window_end
        ]
        window_records.sort(key=lambda r: r.timestamp_unix)

        for r in window_records:
            ConfidenceTagger.tag_real(r)

        filled: list[TelemetryRecord] = list(window_records)

        if window_records:
            if window_records[0].timestamp_unix > window_start + target_interval_seconds:
                gap_duration = window_records[0].timestamp_unix - window_start
                interpolated = self._interpolator.interpolate_gap(
                    before=None,
                    after=window_records[0],
                    gap_duration_seconds=gap_duration,
                    target_interval_seconds=target_interval_seconds,
                    source="backfill.dense_window",
                )
                filled.extend(interpolated)

            for i in range(1, len(window_records)):
                prev = window_records[i - 1]
                curr = window_records[i]
                gap = curr.timestamp_unix - prev.timestamp_unix

                if gap > target_interval_seconds * 2:
                    interpolated = self._interpolator.interpolate_gap(
                        before=prev,
                        after=curr,
                        gap_duration_seconds=gap,
                        target_interval_seconds=target_interval_seconds,
                        source="backfill.dense_window",
                    )
                    filled.extend(interpolated)

        filled.sort(key=lambda r: r.timestamp_unix)
        return filled

    def run_backfill(
        self,
        incident_times: list[str] | None = None,
        window_before_minutes: int = 60,
    ) -> dict[str, Any]:
        """Run the full backfill pipeline and return results."""
        total_loaded = self.load_historical_data()

        validation = self._validator.validate(self._all_records)

        gap_reports = self.detect_all_gaps()

        dense_windows: list[dict[str, Any]] = []
        all_backfilled: list[TelemetryRecord] = []

        targets = incident_times or [
            "2026-05-11T21:49:02.703942+00:00",
            "2026-05-11T22:14:37.782126+00:00",
        ]

        for incident_time in targets:
            window = self.create_dense_window(
                center_time=incident_time,
                window_before_minutes=window_before_minutes,
                window_after_minutes=10,
            )

            real_count = sum(1 for r in window if r.origin == DataOrigin.REAL.value)
            interp_count = sum(1 for r in window if r.origin == DataOrigin.INTERPOLATED.value)
            unknown_count = sum(1 for r in window if r.origin == DataOrigin.UNKNOWN.value)

            dense_windows.append({
                "incident_time": incident_time,
                "window_start": window[0].timestamp if window else "",
                "window_end": window[-1].timestamp if window else "",
                "total_records": len(window),
                "real_records": real_count,
                "interpolated_records": interp_count,
                "unknown_records": unknown_count,
            })

            all_backfilled.extend(window)

        self._backfilled_records = all_backfilled

        confidence_report = ConfidenceTagger.generate_report(all_backfilled)

        total_gaps = sum(r.total_gaps for r in gap_reports.values())
        total_gap_seconds = sum(r.total_gap_seconds for r in gap_reports.values())

        original_coverage = 1.0 - (total_gap_seconds / (64.95 * 3600)) if total_gap_seconds else 1.0
        backfilled_unknowns = sum(1 for r in all_backfilled if r.origin == DataOrigin.UNKNOWN.value)
        backfilled_interpolated = sum(1 for r in all_backfilled if r.origin == DataOrigin.INTERPOLATED.value)
        backfilled_real = sum(1 for r in all_backfilled if r.origin == DataOrigin.REAL.value)

        improvement = 0.0
        if backfilled_real + backfilled_interpolated > 0:
            improvement = (backfilled_interpolated) / max(1, backfilled_real + backfilled_interpolated + backfilled_unknowns)

        results = {
            "backfill_version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "program": "P1.6 Reality Repair Sprint — Phase 5: Historical Backfill",
            "summary": {
                "total_records_processed": total_loaded,
                "total_gaps_detected": total_gaps,
                "total_gap_hours": round(total_gap_seconds / 3600, 2),
                "dense_windows_created": len(dense_windows),
                "total_backfilled_records": len(all_backfilled),
                "original_coverage_ratio": round(max(0, original_coverage), 4),
                "coverage_improvement": round(improvement, 4),
            },
            "validation": validation.to_dict(),
            "gap_reports": {k: v.to_dict() for k, v in gap_reports.items()},
            "dense_windows": dense_windows,
            "confidence_distribution": confidence_report.to_dict(),
            "limitations": [
                "GAP-002 (38h system silence) cannot be backfilled — no source data exists",
                "GAP-003 (somatic attention) cannot be backfilled — attention was not captured",
                "Interpolated values for GAP-001 (8h health blind spot) use nearest-neighbor from archived scratchpad data with decaying confidence",
                "Health score reconstruction is approximate — original scoring formula weights are embedded in the system, not in the interpolation",
                "All interpolated records are transparently tagged and traceable to source data",
            ],
        }

        return results

    def export_backfill_jsonl(self, output_path: Path | None = None) -> str:
        """Export backfilled records as normalized JSONL."""
        path = output_path or (self._root / "telemetry" / "backfill" / "backfilled_records.jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as fh:
            for record in sorted(self._backfilled_records, key=lambda r: r.timestamp_unix):
                fh.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")

        logger.info("Exported %d backfilled records to %s", len(self._backfilled_records), path)
        return str(path)

    def _load_dmn(self) -> int:
        """Load and normalize memory/dmn.jsonl."""
        path = self._root / "memory" / "dmn.jsonl"
        if not path.exists():
            return 0
        count = 0
        with path.open("r", encoding="utf-8") as fh:
            for line_num, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    record = self._normalizer.normalize_dmn_record(data, source_line=line_num)
                    self._all_records.append(record)
                    count += 1
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning("DMN line %d: %s", line_num, e)
        return count

    def _load_actions(self) -> int:
        """Load and normalize logs/actions.jsonl."""
        path = self._root / "logs" / "actions.jsonl"
        if not path.exists():
            return 0
        count = 0
        with path.open("r", encoding="utf-8") as fh:
            for line_num, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    record = self._normalizer.normalize_action_record(data)
                    self._all_records.append(record)
                    count += 1
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning("Actions line %d: %s", line_num, e)
        return count

    def _load_health_scores(self) -> int:
        """Load and normalize guardian/health/health_scores.json history."""
        path = self._root / "guardian" / "health" / "health_scores.json"
        if not path.exists():
            return 0
        count = 0
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            for entry in data.get("history", []):
                record = self._normalizer.normalize_health_record(entry)
                self._all_records.append(record)
                count += 1
            current = data.get("current")
            if current:
                record = self._normalizer.normalize_health_record(current)
                self._all_records.append(record)
                count += 1
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Health scores: %s", e)
        return count

    def _load_incidents(self) -> int:
        """Load and normalize guardian/incidents/index.json."""
        path = self._root / "guardian" / "incidents" / "index.json"
        if not path.exists():
            return 0
        count = 0
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            for incident in data.get("incidents", []):
                record = self._normalizer.normalize_incident_record(incident)
                self._all_records.append(record)
                count += 1
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Incidents: %s", e)
        return count

    def _load_governance(self) -> int:
        """Load and normalize governance/audit/decisions.jsonl."""
        path = self._root / "governance" / "audit" / "decisions.jsonl"
        if not path.exists():
            return 0
        count = 0
        with path.open("r", encoding="utf-8") as fh:
            for line_num, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    record = self._normalizer.normalize_governance_record(data)
                    self._all_records.append(record)
                    count += 1
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning("Governance line %d: %s", line_num, e)
        return count

    def _load_archived_scratchpad(self) -> int:
        """Load and normalize memory/archive/scratchpad_archived.jsonl."""
        path = self._root / "memory" / "archive" / "scratchpad_archived.jsonl"
        if not path.exists():
            return 0
        count = 0
        with path.open("r", encoding="utf-8") as fh:
            for line_num, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    record = self._normalizer.normalize_dmn_record(data, source_line=line_num)
                    record.metadata["archived"] = True
                    self._all_records.append(record)
                    count += 1
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning("Archived scratchpad line %d: %s", line_num, e)
        return count
