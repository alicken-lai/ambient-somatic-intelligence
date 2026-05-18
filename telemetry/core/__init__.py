"""
Telemetry Core — Unified telemetry normalization layer for Ambient OS.

Provides:
  - TelemetryRecord: canonical schema for all telemetry data
  - TelemetryNormalizer: converts heterogeneous sources into TelemetryRecords
  - TimestampValidator: detects ordering anomalies and timezone issues
  - GapDetector: identifies and classifies telemetry gaps
"""

from telemetry.core.telemetry_schema import TelemetryRecord, DataOrigin
from telemetry.core.telemetry_normalizer import TelemetryNormalizer
from telemetry.core.timestamp_validator import TimestampValidator, ValidationResult
from telemetry.core.gap_detector import GapDetector, Gap, GapSeverity

__all__ = [
    "TelemetryRecord",
    "DataOrigin",
    "TelemetryNormalizer",
    "TimestampValidator",
    "ValidationResult",
    "GapDetector",
    "Gap",
    "GapSeverity",
]
