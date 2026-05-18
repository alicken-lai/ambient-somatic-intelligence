"""
Telemetry Backfill — Historical gap detection and interpolation.

Provides:
  - BackfillEngine: orchestrates normalization, gap detection, and filling
  - InterpolationEngine: smart interpolation with confidence decay
  - ConfidenceTagger: tags every record with origin and confidence score
"""

from telemetry.backfill.confidence_tagger import ConfidenceTagger, DataOrigin
from telemetry.backfill.interpolation_engine import InterpolationEngine
from telemetry.backfill.backfill_engine import BackfillEngine

__all__ = [
    "BackfillEngine",
    "InterpolationEngine",
    "ConfidenceTagger",
    "DataOrigin",
]
