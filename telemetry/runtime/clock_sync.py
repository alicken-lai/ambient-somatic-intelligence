"""
Clock Sync Validator — Detects and corrects clock drift in telemetry timestamps.

Important for replay fidelity: if timestamps drift, precursor detection
windows become unreliable.  This module compares system time against a
reference (NTP query or last known-good snapshot) and flags records
collected during drift periods.
"""

from __future__ import annotations

import logging
import socket
import struct
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

_NTP_EPOCH_OFFSET = 2208988800  # seconds between 1900-01-01 and 1970-01-01
_DEFAULT_NTP_SERVERS = [
    "time.apple.com",
    "pool.ntp.org",
    "time.google.com",
]
_NTP_PORT = 123
_NTP_TIMEOUT_SECONDS = 2.0
_DEFAULT_DRIFT_THRESHOLD_SECONDS = 1.0


@dataclass
class DriftMeasurement:
    """A single clock-drift measurement."""
    measured_at: float
    system_time: float
    reference_time: float
    drift_seconds: float
    reference_source: str
    exceeds_threshold: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "measured_at": datetime.fromtimestamp(self.measured_at, tz=timezone.utc).isoformat(),
            "system_time": datetime.fromtimestamp(self.system_time, tz=timezone.utc).isoformat(),
            "reference_time": datetime.fromtimestamp(self.reference_time, tz=timezone.utc).isoformat(),
            "drift_seconds": round(self.drift_seconds, 6),
            "reference_source": self.reference_source,
            "exceeds_threshold": self.exceeds_threshold,
        }


@dataclass
class TimestampAdjustment:
    """Audit record for a timestamp correction."""
    original_timestamp: float
    adjusted_timestamp: float
    drift_applied_seconds: float
    source_name: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "original": datetime.fromtimestamp(self.original_timestamp, tz=timezone.utc).isoformat(),
            "adjusted": datetime.fromtimestamp(self.adjusted_timestamp, tz=timezone.utc).isoformat(),
            "drift_applied_seconds": round(self.drift_applied_seconds, 6),
            "source_name": self.source_name,
            "reason": self.reason,
        }


class ClockSyncValidator:
    """Detects and corrects clock drift in telemetry timestamps.

    Parameters
    ----------
    drift_threshold_seconds:
        Maximum acceptable drift before flagging timestamps.
    ntp_servers:
        List of NTP servers to query, tried in order.
    clock_fn:
        Override for deterministic testing / replay.
    """

    def __init__(
        self,
        drift_threshold_seconds: float = _DEFAULT_DRIFT_THRESHOLD_SECONDS,
        ntp_servers: list[str] | None = None,
        clock_fn=None,
    ):
        self._threshold = drift_threshold_seconds
        self._ntp_servers = ntp_servers or list(_DEFAULT_NTP_SERVERS)
        self._clock = clock_fn or time.time

        self._measurements: list[DriftMeasurement] = []
        self._adjustments: list[TimestampAdjustment] = []
        self._last_known_good: Optional[float] = None
        self._current_drift: float = 0.0
        self._max_measurements = 1000
        self._max_adjustments = 5000

    # ── Drift detection ───────────────────────────────────────────────

    def measure_drift(self) -> DriftMeasurement:
        """Query NTP to measure current clock drift.

        Falls back to ``last_known_good`` reference if NTP is unreachable.
        """
        system_time = self._clock()
        ref_time, ref_source = self._get_reference_time()
        drift = system_time - ref_time

        measurement = DriftMeasurement(
            measured_at=system_time,
            system_time=system_time,
            reference_time=ref_time,
            drift_seconds=drift,
            reference_source=ref_source,
            exceeds_threshold=abs(drift) > self._threshold,
        )

        self._current_drift = drift
        self._measurements.append(measurement)
        if len(self._measurements) > self._max_measurements:
            self._measurements = self._measurements[-self._max_measurements:]

        if not measurement.exceeds_threshold:
            self._last_known_good = system_time

        if measurement.exceeds_threshold:
            logger.warning(
                "Clock drift detected: %.3fs (threshold=%.3fs, source=%s)",
                drift,
                self._threshold,
                ref_source,
            )

        return measurement

    def check_drift(self) -> bool:
        """Quick check: does current drift exceed threshold?"""
        m = self.measure_drift()
        return m.exceeds_threshold

    # ── Timestamp adjustment ──────────────────────────────────────────

    def adjust_timestamp(
        self,
        timestamp: float,
        source_name: str = "unknown",
    ) -> tuple[float, Optional[TimestampAdjustment]]:
        """Adjust a telemetry timestamp if drift is detected.

        Returns ``(adjusted_timestamp, audit_record)``.
        The audit record is None if no adjustment was needed.
        """
        if abs(self._current_drift) <= self._threshold:
            return timestamp, None

        adjusted = timestamp - self._current_drift
        audit = TimestampAdjustment(
            original_timestamp=timestamp,
            adjusted_timestamp=adjusted,
            drift_applied_seconds=-self._current_drift,
            source_name=source_name,
            reason=f"Clock drift {self._current_drift:.3f}s exceeds threshold {self._threshold:.3f}s",
        )

        self._adjustments.append(audit)
        if len(self._adjustments) > self._max_adjustments:
            self._adjustments = self._adjustments[-self._max_adjustments:]

        return adjusted, audit

    def flag_drift_period(
        self,
        start: float,
        end: float,
    ) -> list[DriftMeasurement]:
        """Return all measurements within a time window that exceeded threshold."""
        return [
            m for m in self._measurements
            if start <= m.measured_at <= end and m.exceeds_threshold
        ]

    # ── Per-window drift analysis ─────────────────────────────────────

    def max_drift_in_window(self, start: float, end: float) -> float:
        """Compute maximum absolute drift observed in a time window."""
        relevant = [
            abs(m.drift_seconds)
            for m in self._measurements
            if start <= m.measured_at <= end
        ]
        return max(relevant) if relevant else 0.0

    # ── Reports ───────────────────────────────────────────────────────

    def status(self) -> dict[str, Any]:
        now = self._clock()
        return {
            "current_drift_seconds": round(self._current_drift, 6),
            "threshold_seconds": self._threshold,
            "exceeds_threshold": abs(self._current_drift) > self._threshold,
            "total_measurements": len(self._measurements),
            "total_adjustments": len(self._adjustments),
            "last_known_good": (
                datetime.fromtimestamp(self._last_known_good, tz=timezone.utc).isoformat()
                if self._last_known_good else None
            ),
            "checked_at": datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
        }

    def recent_measurements(self, limit: int = 20) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self._measurements[-limit:]]

    def recent_adjustments(self, limit: int = 20) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self._adjustments[-limit:]]

    # ── NTP query ─────────────────────────────────────────────────────

    def _get_reference_time(self) -> tuple[float, str]:
        """Try NTP servers; fall back to last_known_good or system clock."""
        for server in self._ntp_servers:
            try:
                ref = self._query_ntp(server)
                return ref, f"ntp:{server}"
            except Exception as exc:
                logger.debug("NTP query to %s failed: %s", server, exc)

        if self._last_known_good is not None:
            return self._last_known_good, "last_known_good"

        return self._clock(), "system_clock_fallback"

    @staticmethod
    def _query_ntp(server: str, timeout: float = _NTP_TIMEOUT_SECONDS) -> float:
        """Minimal NTP query (mode 3 client, no authentication).

        Returns server timestamp as seconds since Unix epoch.
        """
        msg = b"\x1b" + 47 * b"\0"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        try:
            sock.sendto(msg, (server, _NTP_PORT))
            data, _ = sock.recvfrom(1024)
        finally:
            sock.close()

        if len(data) < 48:
            raise ValueError(f"NTP response too short: {len(data)} bytes")

        t = struct.unpack("!12I", data)[10]
        t -= _NTP_EPOCH_OFFSET
        return float(t)
