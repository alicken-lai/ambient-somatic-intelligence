"""
Rate Tracker — Event rate monitoring and spike detection.

Monitors the rate of change for signal types over sliding time windows.
Detects rate spikes (>2x baseline) and provides trend analysis:

  - Sliding window rate calculation (events per minute)
  - Baseline rate via exponential moving average
  - Spike detection with configurable multiplier
  - Trend direction: increasing / stable / decreasing

When a spike is detected, the tracker can emit an ALERTNESS signal
onto the bus to propagate the awareness.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from somatic.signal_bus import (
    SomaticSignalBus,
    SomaticSignal,
    SignalType,
    SignalUrgency,
)


@dataclass
class RateWindow:
    """Per-type sliding window for rate calculation."""
    signal_type: SignalType
    timestamps: deque = field(default_factory=lambda: deque(maxlen=1000))
    baseline_rate: float = 0.0
    baseline_samples: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_type": self.signal_type.value,
            "event_count": len(self.timestamps),
            "baseline_rate": round(self.baseline_rate, 4),
            "baseline_samples": self.baseline_samples,
        }


class RateTracker:
    """
    Monitors event rates per signal type and detects spikes.

    Usage:
        bus = SomaticSignalBus()
        tracker = RateTracker(bus)

        tracker.record(SignalType.PAIN)
        rate = tracker.current_rate(SignalType.PAIN)
        is_spike = tracker.is_spike(SignalType.PAIN)
    """

    def __init__(
        self,
        bus: SomaticSignalBus | None = None,
        window_seconds: float = 300.0,
        spike_multiplier: float = 2.0,
        baseline_alpha: float = 0.05,
        min_events_for_spike: int = 3,
        spike_cooldown: float = 60.0,
    ):
        self.bus = bus or SomaticSignalBus()
        self._window_seconds = window_seconds
        self._spike_multiplier = spike_multiplier
        self._baseline_alpha = baseline_alpha
        self._min_events_for_spike = min_events_for_spike
        self._spike_cooldown = spike_cooldown
        self._windows: dict[SignalType, RateWindow] = {}
        self._last_spike_time: dict[SignalType, float] = {}
        self._subscribed = False

    def subscribe(self) -> None:
        """Subscribe to the bus to auto-track all signal rates."""
        if not self._subscribed:
            self.bus.on_any(self._on_signal)
            self._subscribed = True

    def record(self, signal_type: SignalType) -> None:
        """Record an occurrence of a signal type."""
        window = self._get_or_create_window(signal_type)
        now = time.time()
        window.timestamps.append(now)
        self._prune_window(window, now)
        self._update_baseline(window, now)

    def current_rate(self, signal_type: SignalType) -> float:
        """
        Get current event rate (events per minute) within the sliding window.
        """
        window = self._windows.get(signal_type)
        if not window or not window.timestamps:
            return 0.0

        now = time.time()
        self._prune_window(window, now)

        if not window.timestamps:
            return 0.0

        elapsed = now - window.timestamps[0]
        if elapsed < 1.0:
            return float(len(window.timestamps))

        return (len(window.timestamps) / elapsed) * 60.0

    def is_spike(self, signal_type: SignalType) -> bool:
        """
        Check if the current rate constitutes a spike (>multiplier x baseline).
        """
        window = self._windows.get(signal_type)
        if not window:
            return False

        rate = self.current_rate(signal_type)
        if rate < self._min_events_for_spike:
            return False

        if window.baseline_rate <= 0:
            return rate >= self._min_events_for_spike

        return rate >= (window.baseline_rate * self._spike_multiplier)

    def trend(self, signal_type: SignalType) -> str:
        """
        Analyze rate trend: "increasing", "stable", or "decreasing".
        """
        window = self._windows.get(signal_type)
        if not window or len(window.timestamps) < 4:
            return "insufficient_data"

        now = time.time()
        self._prune_window(window, now)

        timestamps = list(window.timestamps)
        if len(timestamps) < 4:
            return "insufficient_data"

        mid = len(timestamps) // 2
        first_half = timestamps[:mid]
        second_half = timestamps[mid:]

        first_span = first_half[-1] - first_half[0] if len(first_half) > 1 else 1.0
        second_span = second_half[-1] - second_half[0] if len(second_half) > 1 else 1.0

        first_rate = len(first_half) / max(first_span, 1.0)
        second_rate = len(second_half) / max(second_span, 1.0)

        if first_rate == 0:
            return "increasing" if second_rate > 0 else "stable"

        ratio = second_rate / first_rate
        if ratio > 1.3:
            return "increasing"
        elif ratio < 0.7:
            return "decreasing"
        return "stable"

    def all_rates(self) -> dict[str, dict[str, Any]]:
        """Get rate summary for all tracked signal types."""
        result: dict[str, dict[str, Any]] = {}
        for sig_type, window in self._windows.items():
            rate = self.current_rate(sig_type)
            result[sig_type.value] = {
                "rate_per_minute": round(rate, 2),
                "baseline_rate": round(window.baseline_rate, 4),
                "is_spike": self.is_spike(sig_type),
                "trend": self.trend(sig_type),
                "event_count": len(window.timestamps),
            }
        return result

    def status(self) -> dict[str, Any]:
        """Current tracker status."""
        spikes = [t.value for t in SignalType if self.is_spike(t)]
        return {
            "subscribed": self._subscribed,
            "tracked_types": len(self._windows),
            "active_spikes": spikes,
            "rates": self.all_rates(),
        }

    def _on_signal(self, signal: SomaticSignal) -> None:
        """Handle incoming bus signal."""
        if signal.source.startswith("rate_tracker."):
            return

        self.record(signal.type)

        if self.is_spike(signal.type):
            last_spike = self._last_spike_time.get(signal.type, 0)
            if (time.time() - last_spike) >= self._spike_cooldown:
                self._last_spike_time[signal.type] = time.time()
                rate = self.current_rate(signal.type)
                window = self._windows[signal.type]
                self.bus.emit(SomaticSignal(
                    type=SignalType.ALERTNESS,
                    urgency=SignalUrgency.HIGH,
                    source=f"rate_tracker.{signal.type.value}",
                    message=(
                        f"Rate spike: {signal.type.value} at "
                        f"{rate:.1f}/min (baseline: {window.baseline_rate:.1f}/min)"
                    ),
                    value=rate,
                    threshold=window.baseline_rate * self._spike_multiplier,
                    metadata={
                        "spike_type": signal.type.value,
                        "current_rate": rate,
                        "baseline_rate": window.baseline_rate,
                        "multiplier": rate / max(window.baseline_rate, 0.001),
                    },
                ))

    def _get_or_create_window(self, signal_type: SignalType) -> RateWindow:
        if signal_type not in self._windows:
            self._windows[signal_type] = RateWindow(signal_type=signal_type)
        return self._windows[signal_type]

    def _prune_window(self, window: RateWindow, now: float) -> None:
        """Discard events outside the sliding window."""
        cutoff = now - self._window_seconds
        while window.timestamps and window.timestamps[0] < cutoff:
            window.timestamps.popleft()

    def _update_baseline(self, window: RateWindow, now: float) -> None:
        """Update the EMA baseline rate."""
        rate = self.current_rate(window.signal_type)
        window.baseline_samples += 1

        if window.baseline_samples == 1:
            window.baseline_rate = rate
        else:
            alpha = self._baseline_alpha
            window.baseline_rate += alpha * (rate - window.baseline_rate)
