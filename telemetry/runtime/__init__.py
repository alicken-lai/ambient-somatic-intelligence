"""
Telemetry Runtime — macOS launchd integration, clock sync, and deduplication.

Provides persistent sampling via LaunchAgent plists, clock-drift detection
for replay fidelity, and duplicate-record suppression.
"""

from telemetry.runtime.launchd_sampling import LaunchdSamplingManager
from telemetry.runtime.clock_sync import ClockSyncValidator
from telemetry.runtime.duplicate_guard import DuplicateGuard

__all__ = [
    "LaunchdSamplingManager",
    "ClockSyncValidator",
    "DuplicateGuard",
]
