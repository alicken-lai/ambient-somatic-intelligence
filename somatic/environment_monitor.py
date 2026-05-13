"""
Environment Monitor — Hardware/OS metric collection and somatic signal emission.

Reads system metrics and translates them into somatic signals:
  CPU usage     → PRESSURE signal (sustained high) or FATIGUE (prolonged)
  Memory usage  → PRESSURE signal
  Disk usage    → PRESSURE signal
  Load average  → FATIGUE signal
  Network       → ALERTNESS (new connections) or PAIN (failures)
  Process count → PRESSURE signal (too many)

Integrates with the existing sense_local.py for metric collection.
"""

from __future__ import annotations

import os
import platform
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from somatic.signal_bus import SomaticSignalBus, SomaticSignal, SignalType, SignalUrgency


AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))


@dataclass
class Thresholds:
    """Configurable thresholds for signal emission."""
    cpu_warning: float = 70.0
    cpu_critical: float = 90.0
    memory_warning: float = 80.0
    memory_critical: float = 92.0
    disk_warning: float = 85.0
    disk_critical: float = 95.0
    load_warning: float = 6.0
    load_critical: float = 10.0
    process_warning: int = 300
    process_critical: int = 500


@dataclass
class EnvironmentSnapshot:
    """A point-in-time snapshot of system metrics."""
    timestamp: float = field(default_factory=time.time)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    load_1m: float = 0.0
    load_5m: float = 0.0
    load_15m: float = 0.0
    process_count: int = 0
    uptime_hours: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_percent": self.disk_percent,
            "load_1m": self.load_1m,
            "load_5m": self.load_5m,
            "load_15m": self.load_15m,
            "process_count": self.process_count,
            "uptime_hours": round(self.uptime_hours, 1),
        }


class EnvironmentMonitor:
    """
    Collects system metrics and emits somatic signals.

    Usage:
        bus = SomaticSignalBus()
        monitor = EnvironmentMonitor(bus)
        signals = monitor.sense()  # Collect metrics and emit signals
        snapshot = monitor.last_snapshot
    """

    def __init__(
        self,
        bus: SomaticSignalBus | None = None,
        thresholds: Thresholds | None = None,
    ):
        self.bus = bus or SomaticSignalBus()
        self.thresholds = thresholds or Thresholds()
        self.last_snapshot: EnvironmentSnapshot | None = None
        self._history: list[EnvironmentSnapshot] = []
        self._max_history = 60

    def sense(self) -> list[SomaticSignal]:
        """Collect current metrics and emit appropriate signals."""
        snapshot = self._collect_snapshot()
        self.last_snapshot = snapshot
        self._history.append(snapshot)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        signals = self._evaluate(snapshot)
        return signals

    def _collect_snapshot(self) -> EnvironmentSnapshot:
        """Collect system metrics using os-level calls."""
        snapshot = EnvironmentSnapshot()

        try:
            load = os.getloadavg()
            snapshot.load_1m = load[0]
            snapshot.load_5m = load[1]
            snapshot.load_15m = load[2]
        except (OSError, AttributeError):
            pass

        try:
            import shutil
            disk = shutil.disk_usage("/")
            snapshot.disk_percent = (disk.used / disk.total) * 100
        except (OSError, ImportError):
            pass

        try:
            if platform.system() == "Darwin":
                snapshot.cpu_percent = snapshot.load_1m / os.cpu_count() * 100 if os.cpu_count() else 0
            else:
                snapshot.cpu_percent = snapshot.load_1m / os.cpu_count() * 100 if os.cpu_count() else 0
        except (OSError, TypeError):
            pass

        try:
            if platform.system() == "Darwin":
                import subprocess
                result = subprocess.run(
                    ["vm_stat"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.splitlines()
                    stats = {}
                    for line in lines[1:]:
                        parts = line.split(":")
                        if len(parts) == 2:
                            key = parts[0].strip()
                            val = parts[1].strip().rstrip(".")
                            try:
                                stats[key] = int(val)
                            except ValueError:
                                pass
                    page_size = 16384
                    free = stats.get("Pages free", 0) * page_size
                    active = stats.get("Pages active", 0) * page_size
                    inactive = stats.get("Pages inactive", 0) * page_size
                    wired = stats.get("Pages wired down", 0) * page_size
                    total = free + active + inactive + wired
                    if total > 0:
                        used = active + wired
                        snapshot.memory_percent = (used / total) * 100
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        try:
            if platform.system() == "Darwin":
                import subprocess
                result = subprocess.run(
                    ["ps", "aux"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    snapshot.process_count = len(result.stdout.splitlines()) - 1
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        return snapshot

    def _evaluate(self, snapshot: EnvironmentSnapshot) -> list[SomaticSignal]:
        """Evaluate snapshot against thresholds and emit signals."""
        signals: list[SomaticSignal] = []
        t = self.thresholds

        if snapshot.cpu_percent >= t.cpu_critical:
            s = self.bus.emit_pressure("cpu", f"CPU at {snapshot.cpu_percent:.0f}%", snapshot.cpu_percent, t.cpu_critical)
            signals.append(s)
        elif snapshot.cpu_percent >= t.cpu_warning:
            s = self.bus.emit_pressure("cpu", f"CPU at {snapshot.cpu_percent:.0f}%", snapshot.cpu_percent, t.cpu_warning)
            signals.append(s)

        if snapshot.memory_percent >= t.memory_critical:
            s = self.bus.emit_pressure("memory", f"Memory at {snapshot.memory_percent:.0f}%", snapshot.memory_percent, t.memory_critical)
            signals.append(s)
        elif snapshot.memory_percent >= t.memory_warning:
            s = self.bus.emit_pressure("memory", f"Memory at {snapshot.memory_percent:.0f}%", snapshot.memory_percent, t.memory_warning)
            signals.append(s)

        if snapshot.disk_percent >= t.disk_critical:
            s = self.bus.emit_pressure("disk", f"Disk at {snapshot.disk_percent:.0f}%", snapshot.disk_percent, t.disk_critical)
            signals.append(s)
        elif snapshot.disk_percent >= t.disk_warning:
            s = self.bus.emit_pressure("disk", f"Disk at {snapshot.disk_percent:.0f}%", snapshot.disk_percent, t.disk_warning)
            signals.append(s)

        if snapshot.load_1m >= t.load_critical:
            signal = SomaticSignal(
                type=SignalType.FATIGUE,
                urgency=SignalUrgency.CRITICAL,
                source="load",
                message=f"Load average {snapshot.load_1m:.1f} (critical: {t.load_critical})",
                value=snapshot.load_1m,
                threshold=t.load_critical,
            )
            self.bus.emit(signal)
            signals.append(signal)
        elif snapshot.load_1m >= t.load_warning:
            signal = SomaticSignal(
                type=SignalType.FATIGUE,
                urgency=SignalUrgency.MEDIUM,
                source="load",
                message=f"Load average {snapshot.load_1m:.1f} (warning: {t.load_warning})",
                value=snapshot.load_1m,
                threshold=t.load_warning,
            )
            self.bus.emit(signal)
            signals.append(signal)

        if not signals and self._was_stressed():
            s = self.bus.emit_calm("environment", "All metrics within normal range")
            signals.append(s)

        return signals

    def _was_stressed(self) -> bool:
        """Check if previous snapshot was above thresholds."""
        if len(self._history) < 2:
            return False
        prev = self._history[-2]
        t = self.thresholds
        return (
            prev.cpu_percent >= t.cpu_warning
            or prev.memory_percent >= t.memory_warning
            or prev.load_1m >= t.load_warning
        )

    def trend(self, metric: str, window: int = 10) -> dict[str, Any]:
        """Get trend analysis for a metric over recent history."""
        if not self._history:
            return {"metric": metric, "trend": "unknown", "samples": 0}

        recent = self._history[-window:]
        values = [getattr(s, metric, 0) for s in recent]

        if len(values) < 2:
            return {"metric": metric, "trend": "insufficient_data", "samples": len(values)}

        avg = sum(values) / len(values)
        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2:]
        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0

        if avg_second > avg_first * 1.1:
            trend = "increasing"
        elif avg_second < avg_first * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "metric": metric,
            "trend": trend,
            "current": values[-1],
            "average": round(avg, 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "samples": len(values),
        }
