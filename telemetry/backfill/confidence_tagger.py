"""
Confidence Tagger — Tags every record with origin and confidence score.

Ensures full auditability: every record in a backfilled dataset carries
a transparent label indicating whether it was observed, computed, or unknown.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from telemetry.core.telemetry_schema import TelemetryRecord, DataOrigin


@dataclass
class ConfidenceReport:
    """Distribution of confidence scores across a dataset."""
    total_records: int = 0
    real_count: int = 0
    interpolated_count: int = 0
    unknown_count: int = 0
    avg_confidence: float = 0.0
    min_confidence: float = 1.0
    max_confidence: float = 0.0
    confidence_histogram: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_records": self.total_records,
            "origin_distribution": {
                "REAL": self.real_count,
                "INTERPOLATED": self.interpolated_count,
                "UNKNOWN": self.unknown_count,
            },
            "confidence": {
                "avg": round(self.avg_confidence, 4),
                "min": round(self.min_confidence, 4),
                "max": round(self.max_confidence, 4),
            },
            "confidence_histogram": self.confidence_histogram,
        }


class ConfidenceTagger:
    """Tags records with origin and computes confidence scores."""

    @staticmethod
    def tag_real(record: TelemetryRecord) -> TelemetryRecord:
        """Tag a record as directly observed real data."""
        record.origin = DataOrigin.REAL.value
        record.confidence = 1.0
        return record

    @staticmethod
    def tag_interpolated(
        record: TelemetryRecord,
        distance_to_nearest_real_seconds: float,
        interpolation_method: str,
        source_count: int = 1,
    ) -> TelemetryRecord:
        """Tag a record as interpolated with computed confidence.

        Confidence decays with distance from the nearest real data point:
          - < 5 min: 0.85-0.95
          - 5-30 min: 0.60-0.85
          - 30-60 min: 0.30-0.60
          - > 60 min: should not be interpolated (use UNKNOWN)

        Higher source_count boosts confidence slightly.
        """
        record.origin = DataOrigin.INTERPOLATED.value

        base = 0.95 * math.exp(-distance_to_nearest_real_seconds / 1800.0)

        method_bonus = {
            "linear": 0.0,
            "nearest_neighbor": -0.05,
            "weighted_average": 0.05,
        }.get(interpolation_method, 0.0)

        source_bonus = min(0.05, (source_count - 1) * 0.02)

        confidence = max(0.05, min(0.95, base + method_bonus + source_bonus))
        record.confidence = round(confidence, 4)

        record.metadata["interpolation"] = {
            "method": interpolation_method,
            "distance_seconds": round(distance_to_nearest_real_seconds, 2),
            "source_count": source_count,
        }

        return record

    @staticmethod
    def tag_unknown(record: TelemetryRecord, reason: str = "gap_too_large") -> TelemetryRecord:
        """Tag a record as unknown — gap too large to interpolate."""
        record.origin = DataOrigin.UNKNOWN.value
        record.confidence = 0.0
        record.metadata["unknown_reason"] = reason
        return record

    @staticmethod
    def generate_report(records: list[TelemetryRecord]) -> ConfidenceReport:
        """Generate a confidence distribution report for a dataset."""
        report = ConfidenceReport()
        total_confidence = 0.0

        for record in records:
            report.total_records += 1
            total_confidence += record.confidence

            if record.confidence < report.min_confidence:
                report.min_confidence = record.confidence
            if record.confidence > report.max_confidence:
                report.max_confidence = record.confidence

            if record.origin == DataOrigin.REAL.value:
                report.real_count += 1
            elif record.origin == DataOrigin.INTERPOLATED.value:
                report.interpolated_count += 1
            else:
                report.unknown_count += 1

            bucket = f"{int(record.confidence * 10) * 10}%"
            report.confidence_histogram[bucket] = report.confidence_histogram.get(bucket, 0) + 1

        if report.total_records > 0:
            report.avg_confidence = total_confidence / report.total_records

        if report.total_records == 0:
            report.min_confidence = 0.0

        return report
