"""
Somatic Signal Bus — Pub/sub event bus for somatic signals.

The SignalBus is the central nervous system of the Ambient OS:
  - Producers emit signals (environment monitor, anomaly detector, etc.)
  - Consumers subscribe to signal types and react
  - Signals carry urgency levels that influence attention allocation
  - History is maintained for pattern detection

Signal types map to bodily metaphors:
  PRESSURE   — resource exhaustion (memory, disk, CPU)
  PAIN       — errors, failures, crashes
  FATIGUE    — prolonged high load, degradation
  ALERTNESS  — new events, external stimuli
  CALM       — system returning to baseline
  REFLEX     — immediate automated response triggered
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class SignalType(str, Enum):
    PRESSURE = "pressure"
    PAIN = "pain"
    FATIGUE = "fatigue"
    ALERTNESS = "alertness"
    CALM = "calm"
    REFLEX = "reflex"


class SignalUrgency(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


@dataclass
class SomaticSignal:
    """A single somatic event signal."""
    type: SignalType
    urgency: SignalUrgency
    source: str
    message: str
    value: float = 0.0
    threshold: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    @property
    def is_critical(self) -> bool:
        return self.urgency >= SignalUrgency.CRITICAL

    @property
    def exceeds_threshold(self) -> bool:
        return self.value > self.threshold if self.threshold else False

    @property
    def age_seconds(self) -> float:
        return time.time() - self.timestamp

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "urgency": self.urgency.value,
            "source": self.source,
            "message": self.message,
            "value": self.value,
            "threshold": self.threshold,
            "metadata": self.metadata,
            "timestamp": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
        }


SignalHandler = Callable[[SomaticSignal], None]


class SomaticSignalBus:
    """
    Central nervous system event bus.

    Usage:
        bus = SomaticSignalBus()

        # Subscribe
        bus.on(SignalType.PRESSURE, handle_pressure)
        bus.on(SignalType.PAIN, handle_errors)
        bus.on_any(log_all_signals)

        # Emit
        bus.emit(SomaticSignal(
            type=SignalType.PRESSURE,
            urgency=SignalUrgency.HIGH,
            source="memory_monitor",
            message="Memory usage at 92%",
            value=92.0,
            threshold=85.0,
        ))
    """

    def __init__(self, history_size: int = 200):
        self._handlers: dict[SignalType, list[SignalHandler]] = {t: [] for t in SignalType}
        self._any_handlers: list[SignalHandler] = []
        self._history: deque[SomaticSignal] = deque(maxlen=history_size)
        self._stats: dict[str, int] = {t.value: 0 for t in SignalType}
        self._muted: set[SignalType] = set()

    def on(self, signal_type: SignalType, handler: SignalHandler) -> None:
        """Subscribe to a specific signal type."""
        self._handlers[signal_type].append(handler)

    def on_guarded(
        self,
        signal_type: SignalType,
        handler: SignalHandler,
        *,
        source: str,
        allowed_writes: frozenset[str] | None = None,
    ) -> SignalHandler:
        """Subscribe with CallbackGuard wrapping (v0.4.4 opt-in)."""
        try:
            from kernel.isolation.guarded_callback import GuardedCallback

            guarded = GuardedCallback()
            wrapped = guarded.register(
                f"somatic:{signal_type.value}",
                handler,
                source=source,
                allowed_writes=allowed_writes,
            )
            self._handlers[signal_type].append(wrapped)
            return wrapped
        except ImportError:
            self._handlers[signal_type].append(handler)
            return handler

    def on_any(self, handler: SignalHandler) -> None:
        """Subscribe to all signals."""
        self._any_handlers.append(handler)

    def off_any(self, handler: SignalHandler) -> None:
        """Unsubscribe from all-signals handlers."""
        if handler in self._any_handlers:
            self._any_handlers.remove(handler)

    def off(self, signal_type: SignalType, handler: SignalHandler) -> None:
        """Unsubscribe from a signal type."""
        handlers = self._handlers.get(signal_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def mute(self, signal_type: SignalType) -> None:
        """Temporarily suppress a signal type."""
        self._muted.add(signal_type)

    def unmute(self, signal_type: SignalType) -> None:
        """Resume a muted signal type."""
        self._muted.discard(signal_type)

    def emit(self, signal: SomaticSignal) -> int:
        """
        Emit a signal to all subscribers.

        Returns the number of handlers that received the signal.
        """
        self._history.append(signal)
        self._stats[signal.type.value] = self._stats.get(signal.type.value, 0) + 1

        if signal.type in self._muted:
            return 0

        notified = 0

        for handler in self._handlers.get(signal.type, []):
            try:
                handler(signal)
                notified += 1
            except Exception:
                pass

        for handler in self._any_handlers:
            try:
                handler(signal)
                notified += 1
            except Exception:
                pass

        return notified

    def emit_pressure(self, source: str, message: str, value: float, threshold: float) -> SomaticSignal:
        """Convenience: emit a PRESSURE signal."""
        urgency = self._urgency_from_ratio(value, threshold)
        signal = SomaticSignal(
            type=SignalType.PRESSURE,
            urgency=urgency,
            source=source,
            message=message,
            value=value,
            threshold=threshold,
        )
        self.emit(signal)
        return signal

    def emit_pain(self, source: str, message: str, urgency: SignalUrgency = SignalUrgency.MEDIUM) -> SomaticSignal:
        """Convenience: emit a PAIN signal (error/failure)."""
        signal = SomaticSignal(
            type=SignalType.PAIN,
            urgency=urgency,
            source=source,
            message=message,
        )
        self.emit(signal)
        return signal

    def emit_calm(self, source: str, message: str = "Returning to baseline") -> SomaticSignal:
        """Convenience: emit a CALM signal (recovery)."""
        signal = SomaticSignal(
            type=SignalType.CALM,
            urgency=SignalUrgency.LOW,
            source=source,
            message=message,
        )
        self.emit(signal)
        return signal

    def recent(self, signal_type: SignalType | None = None, seconds: float = 60) -> list[SomaticSignal]:
        """Get recent signals within a time window."""
        cutoff = time.time() - seconds
        signals = [s for s in self._history if s.timestamp >= cutoff]
        if signal_type:
            signals = [s for s in signals if s.type == signal_type]
        return signals

    def current_state(self) -> dict[str, Any]:
        """Get current somatic state summary."""
        now = time.time()
        recent_60s = [s for s in self._history if now - s.timestamp < 60]
        recent_critical = [s for s in recent_60s if s.is_critical]

        dominant_type = None
        if recent_60s:
            type_counts = {}
            for s in recent_60s:
                type_counts[s.type] = type_counts.get(s.type, 0) + 1
            dominant_type = max(type_counts, key=type_counts.get)

        return {
            "total_signals": sum(self._stats.values()),
            "signals_last_60s": len(recent_60s),
            "critical_last_60s": len(recent_critical),
            "dominant_signal": dominant_type.value if dominant_type else "calm",
            "by_type": dict(self._stats),
            "muted": [t.value for t in self._muted],
        }

    @staticmethod
    def _urgency_from_ratio(value: float, threshold: float) -> SignalUrgency:
        """Derive urgency from how much value exceeds threshold."""
        if threshold <= 0:
            return SignalUrgency.LOW
        ratio = value / threshold
        if ratio >= 1.3:
            return SignalUrgency.CRITICAL
        elif ratio >= 1.15:
            return SignalUrgency.HIGH
        elif ratio >= 1.0:
            return SignalUrgency.MEDIUM
        return SignalUrgency.LOW
