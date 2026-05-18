"""
Interpolation Engine — Smart interpolation for telemetry gaps.

Rules:
  - Short gaps (< 10 min): linear interpolation from neighboring values
  - Medium gaps (10-60 min): weighted interpolation with decay
  - Long gaps (> 60 min): mark as UNKNOWN, no interpolation
  - Never silently replaces real data
  - Always tags interpolated values with confidence score
"""

from __future__ import annotations

import uuid
from typing import Any

from telemetry.core.telemetry_schema import TelemetryRecord, DataOrigin
from telemetry.backfill.confidence_tagger import ConfidenceTagger


class InterpolationEngine:
    """Generates interpolated records for detected gaps."""

    def __init__(self, max_interpolation_seconds: float = 3600.0):
        self._max_interpolation = max_interpolation_seconds
        self._tagger = ConfidenceTagger()
        self._interpolated_count = 0

    def interpolate_gap(
        self,
        before: TelemetryRecord | None,
        after: TelemetryRecord | None,
        gap_duration_seconds: float,
        target_interval_seconds: float = 60.0,
        source: str = "backfill",
    ) -> list[TelemetryRecord]:
        """Generate interpolated records to fill a gap.

        Returns an empty list for gaps > max_interpolation_seconds.
        """
        if gap_duration_seconds > self._max_interpolation:
            return self._mark_unknown_gap(before, after, gap_duration_seconds, source)

        if not before and not after:
            return []

        if gap_duration_seconds <= 0:
            return []

        num_points = max(1, int(gap_duration_seconds / target_interval_seconds))
        records: list[TelemetryRecord] = []

        start_unix = before.timestamp_unix if before else (after.timestamp_unix - gap_duration_seconds)
        end_unix = after.timestamp_unix if after else (before.timestamp_unix + gap_duration_seconds)
        step = (end_unix - start_unix) / (num_points + 1)

        for i in range(1, num_points + 1):
            t = start_unix + step * i
            ratio = i / (num_points + 1)

            if gap_duration_seconds < 600:
                payload = self._linear_interpolate(before, after, ratio)
                method = "linear"
            else:
                payload = self._weighted_interpolate(before, after, ratio)
                method = "weighted_average"

            from datetime import datetime, timezone
            ts_dt = datetime.fromtimestamp(t, tz=timezone.utc)

            distance = min(
                t - start_unix if before else float("inf"),
                end_unix - t if after else float("inf"),
            )

            record = TelemetryRecord(
                record_id=uuid.uuid4().hex[:16],
                source=source,
                timestamp=ts_dt.isoformat(),
                timestamp_unix=t,
                category=before.category if before else (after.category if after else "metric"),
                payload=payload,
                confidence=1.0,
                origin=DataOrigin.INTERPOLATED.value,
                metadata={
                    "backfill_source": "interpolation_engine",
                    "gap_duration_seconds": round(gap_duration_seconds, 2),
                    "position_in_gap": i,
                    "total_interpolated": num_points,
                },
            )

            ConfidenceTagger.tag_interpolated(
                record,
                distance_to_nearest_real_seconds=distance,
                interpolation_method=method,
                source_count=sum([1 if before else 0, 1 if after else 0]),
            )

            records.append(record)
            self._interpolated_count += 1

        return records

    def _linear_interpolate(
        self,
        before: TelemetryRecord | None,
        after: TelemetryRecord | None,
        ratio: float,
    ) -> dict[str, Any]:
        """Linear interpolation between two payloads for numeric fields."""
        if not before or not after:
            return (before or after).payload.copy() if (before or after) else {}

        result: dict[str, Any] = {}
        all_keys = set(before.payload.keys()) | set(after.payload.keys())

        for key in all_keys:
            v_before = before.payload.get(key)
            v_after = after.payload.get(key)

            if isinstance(v_before, (int, float)) and isinstance(v_after, (int, float)):
                result[key] = round(v_before + (v_after - v_before) * ratio, 4)
            elif v_before is not None:
                result[key] = v_before
            else:
                result[key] = v_after

        return result

    def _weighted_interpolate(
        self,
        before: TelemetryRecord | None,
        after: TelemetryRecord | None,
        ratio: float,
    ) -> dict[str, Any]:
        """Weighted interpolation with decay toward the center of the gap.

        Points closer to a real boundary get more weight from that boundary.
        Center of gap gets averaged values with lower confidence.
        """
        if not before or not after:
            return (before or after).payload.copy() if (before or after) else {}

        decay = 1.0 - 2.0 * abs(ratio - 0.5)
        weight_before = (1.0 - ratio) * (1.0 + 0.2 * decay)
        weight_after = ratio * (1.0 + 0.2 * decay)
        total_weight = weight_before + weight_after

        result: dict[str, Any] = {}
        all_keys = set(before.payload.keys()) | set(after.payload.keys())

        for key in all_keys:
            v_before = before.payload.get(key)
            v_after = after.payload.get(key)

            if isinstance(v_before, (int, float)) and isinstance(v_after, (int, float)):
                interpolated = (v_before * weight_before + v_after * weight_after) / total_weight
                result[key] = round(interpolated, 4)
            elif v_before is not None:
                result[key] = v_before
            else:
                result[key] = v_after

        return result

    def _mark_unknown_gap(
        self,
        before: TelemetryRecord | None,
        after: TelemetryRecord | None,
        gap_duration_seconds: float,
        source: str,
    ) -> list[TelemetryRecord]:
        """Create boundary markers for gaps too large to interpolate."""
        from datetime import datetime, timezone

        records = []

        if before:
            start_unix = before.timestamp_unix + 1
            ts_dt = datetime.fromtimestamp(start_unix, tz=timezone.utc)
            marker = TelemetryRecord(
                record_id=uuid.uuid4().hex[:16],
                source=source,
                timestamp=ts_dt.isoformat(),
                timestamp_unix=start_unix,
                category="state",
                payload={
                    "gap_marker": "start",
                    "gap_duration_seconds": round(gap_duration_seconds, 2),
                    "reason": "gap_too_large_to_interpolate",
                },
                confidence=0.0,
                origin=DataOrigin.UNKNOWN.value,
                metadata={"backfill_source": "interpolation_engine"},
            )
            records.append(marker)

        if after:
            end_unix = after.timestamp_unix - 1
            ts_dt = datetime.fromtimestamp(end_unix, tz=timezone.utc)
            marker = TelemetryRecord(
                record_id=uuid.uuid4().hex[:16],
                source=source,
                timestamp=ts_dt.isoformat(),
                timestamp_unix=end_unix,
                category="state",
                payload={
                    "gap_marker": "end",
                    "gap_duration_seconds": round(gap_duration_seconds, 2),
                    "reason": "gap_too_large_to_interpolate",
                },
                confidence=0.0,
                origin=DataOrigin.UNKNOWN.value,
                metadata={"backfill_source": "interpolation_engine"},
            )
            records.append(marker)

        return records

    @property
    def interpolated_count(self) -> int:
        return self._interpolated_count
