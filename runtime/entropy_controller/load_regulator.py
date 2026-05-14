"""
Load Regulator — Global rate limiting and backpressure at queue boundaries.

Prevents the feedback loop: throttle → queue buildup → stress → more throttle.
Implements per-type and global signal rate limits with a sliding time window,
plus queue backpressure with hysteresis to prevent oscillation.

Rate enforcement uses timestamp deques per signal type. Hysteresis means once
throttle engages, pressure must drop below (threshold - hysteresis_factor)
before the throttle releases.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LoadConfig:
    """Rate limiting and backpressure configuration."""
    global_signal_rate_limit: int = 100
    per_type_rate_limit: int = 30
    rate_window_seconds: float = 60.0
    queue_pressure_threshold: float = 0.8
    hysteresis_factor: float = 0.1


@dataclass
class RateCheckResult:
    """Result of a signal rate check."""
    signal_type: str
    current_rate: float
    limit: float
    allowed: bool
    window_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_type": self.signal_type,
            "current_rate": round(self.current_rate, 2),
            "limit": self.limit,
            "allowed": self.allowed,
            "window_seconds": self.window_seconds,
        }


@dataclass
class PressureResult:
    """Result of a queue pressure evaluation."""
    queue_name: str
    depth: int
    capacity: int
    pressure: float
    action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "queue_name": self.queue_name,
            "depth": self.depth,
            "capacity": self.capacity,
            "pressure": round(self.pressure, 4),
            "action": self.action,
        }


@dataclass
class ThrottleRecommendation:
    """Overall throttle recommendation based on current load."""
    should_throttle: bool
    level: str
    reason: str
    current_pressure: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "should_throttle": self.should_throttle,
            "level": self.level,
            "reason": self.reason,
            "current_pressure": round(self.current_pressure, 4),
        }


class LoadRegulator:
    """
    Global rate limiter with sliding-window signal tracking and queue backpressure.

    Usage:
        reg = LoadRegulator()
        reg.record_signal("PRESSURE")
        result = reg.check_signal_rate("PRESSURE")
        pressure = reg.check_queue_pressure("task_queue", depth=80, capacity=100)
        rec = reg.get_throttle_recommendation()
    """

    def __init__(self, config: LoadConfig | None = None) -> None:
        self._config = config or LoadConfig()
        self._signal_windows: dict[str, deque[float]] = {}
        self._global_window: deque[float] = deque()
        self._queue_states: dict[str, PressureResult] = {}
        self._throttle_engaged: bool = False

    def record_signal(self, signal_type: str) -> None:
        now = time.monotonic()

        if signal_type not in self._signal_windows:
            self._signal_windows[signal_type] = deque()
        self._signal_windows[signal_type].append(now)
        self._global_window.append(now)

        self._prune_window(self._signal_windows[signal_type], now)
        self._prune_window(self._global_window, now)

    def check_signal_rate(self, signal_type: str) -> RateCheckResult:
        now = time.monotonic()

        type_window = self._signal_windows.get(signal_type, deque())
        self._prune_window(type_window, now)

        window_secs = self._config.rate_window_seconds
        current_rate = len(type_window) * (60.0 / window_secs) if window_secs > 0 else 0.0

        self._prune_window(self._global_window, now)
        global_rate = len(self._global_window) * (60.0 / window_secs) if window_secs > 0 else 0.0

        type_allowed = current_rate <= self._config.per_type_rate_limit
        global_allowed = global_rate <= self._config.global_signal_rate_limit
        allowed = type_allowed and global_allowed

        effective_limit = min(
            self._config.per_type_rate_limit,
            self._config.global_signal_rate_limit,
        )

        return RateCheckResult(
            signal_type=signal_type,
            current_rate=current_rate,
            limit=float(effective_limit),
            allowed=allowed,
            window_seconds=window_secs,
        )

    def check_queue_pressure(
        self,
        queue_name: str,
        depth: int,
        capacity: int,
    ) -> PressureResult:
        if capacity <= 0:
            pressure = 1.0
        else:
            pressure = depth / capacity

        threshold = self._config.queue_pressure_threshold
        hysteresis = self._config.hysteresis_factor

        if pressure >= 0.95:
            action = "shed_load"
        elif self._throttle_engaged:
            release_point = threshold - hysteresis
            if pressure < release_point:
                action = "accept"
                self._throttle_engaged = False
            else:
                action = "throttle"
        elif pressure >= threshold:
            action = "throttle"
            self._throttle_engaged = True
        else:
            action = "accept"

        result = PressureResult(
            queue_name=queue_name,
            depth=depth,
            capacity=capacity,
            pressure=pressure,
            action=action,
        )
        self._queue_states[queue_name] = result
        return result

    def get_throttle_recommendation(self) -> ThrottleRecommendation:
        now = time.monotonic()
        self._prune_window(self._global_window, now)

        window_secs = self._config.rate_window_seconds
        global_rate = len(self._global_window) * (60.0 / window_secs) if window_secs > 0 else 0.0
        rate_pressure = global_rate / max(self._config.global_signal_rate_limit, 1)

        queue_pressures = [r.pressure for r in self._queue_states.values()]
        max_queue_pressure = max(queue_pressures) if queue_pressures else 0.0

        current_pressure = max(rate_pressure, max_queue_pressure)

        if current_pressure > 0.95:
            return ThrottleRecommendation(
                should_throttle=True,
                level="heavy",
                reason=f"System pressure at {current_pressure:.0%} — shed non-critical load",
                current_pressure=current_pressure,
            )
        if current_pressure > self._config.queue_pressure_threshold:
            return ThrottleRecommendation(
                should_throttle=True,
                level="moderate",
                reason=f"System pressure at {current_pressure:.0%} — reduce throughput",
                current_pressure=current_pressure,
            )
        if self._throttle_engaged:
            release = self._config.queue_pressure_threshold - self._config.hysteresis_factor
            if current_pressure < release:
                self._throttle_engaged = False
                return ThrottleRecommendation(
                    should_throttle=False,
                    level="none",
                    reason=f"Pressure dropped to {current_pressure:.0%} — below hysteresis release point",
                    current_pressure=current_pressure,
                )
            return ThrottleRecommendation(
                should_throttle=True,
                level="mild",
                reason=f"Throttle still engaged — pressure {current_pressure:.0%} above release point {release:.0%}",
                current_pressure=current_pressure,
            )

        return ThrottleRecommendation(
            should_throttle=False,
            level="none",
            reason=f"System pressure nominal at {current_pressure:.0%}",
            current_pressure=current_pressure,
        )

    def reset(self) -> None:
        self._signal_windows.clear()
        self._global_window.clear()
        self._queue_states.clear()
        self._throttle_engaged = False
        logger.info("LoadRegulator reset — all rate windows and queue states cleared")

    def _prune_window(self, window: deque[float], now: float) -> None:
        cutoff = now - self._config.rate_window_seconds
        while window and window[0] < cutoff:
            window.popleft()
