"""
Attention Manager — Cognitive attention allocation based on somatic signals.

Maps signal urgency to system behavior adjustments:
  - FOCUSED:   Normal operation, full capability
  - ALERT:     Increased monitoring, cautious execution
  - STRESSED:  Context compression active, reduce parallelism
  - OVERWHELMED: Emergency mode, pause non-critical tasks, notify operator

The AttentionManager integrates with:
  - ContextBudgetManager: reduce budgets under stress
  - TaskGraph Scheduler: reduce concurrency under load
  - Governance: increase scrutiny when system is stressed
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any, Callable

from somatic.signal_bus import SomaticSignalBus, SomaticSignal, SignalType, SignalUrgency


class AttentionLevel(IntEnum):
    FOCUSED = 0
    ALERT = 1
    STRESSED = 2
    OVERWHELMED = 3

    @property
    def label(self) -> str:
        return self.name.lower()


@dataclass
class AttentionState:
    """Current attention state with derived configuration."""
    level: AttentionLevel
    reason: str
    since: float = field(default_factory=time.time)
    active_signals: int = 0
    critical_signals: int = 0

    @property
    def max_concurrency(self) -> int:
        return {
            AttentionLevel.FOCUSED: 5,
            AttentionLevel.ALERT: 3,
            AttentionLevel.STRESSED: 2,
            AttentionLevel.OVERWHELMED: 1,
        }[self.level]

    @property
    def context_budget_ratio(self) -> float:
        """Ratio of normal context budget to use."""
        return {
            AttentionLevel.FOCUSED: 1.0,
            AttentionLevel.ALERT: 0.85,
            AttentionLevel.STRESSED: 0.65,
            AttentionLevel.OVERWHELMED: 0.4,
        }[self.level]

    @property
    def governance_sensitivity(self) -> float:
        """Multiplier for governance strictness (higher = stricter)."""
        return {
            AttentionLevel.FOCUSED: 1.0,
            AttentionLevel.ALERT: 1.2,
            AttentionLevel.STRESSED: 1.5,
            AttentionLevel.OVERWHELMED: 2.0,
        }[self.level]

    @property
    def should_pause_non_critical(self) -> bool:
        return self.level >= AttentionLevel.OVERWHELMED

    @property
    def should_notify_operator(self) -> bool:
        return self.level >= AttentionLevel.STRESSED

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level.label,
            "level_value": int(self.level),
            "reason": self.reason,
            "since": datetime.fromtimestamp(self.since, tz=timezone.utc).isoformat(),
            "duration_seconds": round(time.time() - self.since, 1),
            "active_signals": self.active_signals,
            "critical_signals": self.critical_signals,
            "max_concurrency": self.max_concurrency,
            "context_budget_ratio": self.context_budget_ratio,
            "governance_sensitivity": self.governance_sensitivity,
            "should_pause_non_critical": self.should_pause_non_critical,
            "should_notify_operator": self.should_notify_operator,
        }


AttentionCallback = Callable[[AttentionState, AttentionState], None]  # (old_state, new_state)


class AttentionManager:
    """
    Manages system attention level based on somatic signals.

    Usage:
        bus = SomaticSignalBus()
        attention = AttentionManager(bus)

        # Register callbacks for attention changes
        attention.on_change(lambda old, new: print(f"Attention: {old.level} → {new.level}"))

        # The manager auto-updates when signals arrive on the bus
        state = attention.current_state()
        print(f"Level: {state.level.label}, Max concurrency: {state.max_concurrency}")
    """

    def __init__(self, bus: SomaticSignalBus | None = None):
        self.bus = bus or SomaticSignalBus()
        self._state = AttentionState(level=AttentionLevel.FOCUSED, reason="Initial state")
        self._callbacks: list[AttentionCallback] = []
        self._signal_window: float = 120.0  # seconds to consider

        self.bus.on_any(self._on_signal)

    def on_change(self, callback: AttentionCallback) -> None:
        """Register callback for attention level changes."""
        self._callbacks.append(callback)

    def current_state(self) -> AttentionState:
        """Get current attention state."""
        return self._state

    def force_level(self, level: AttentionLevel, reason: str) -> None:
        """Manually override attention level."""
        old = self._state
        self._state = AttentionState(level=level, reason=f"Manual: {reason}")
        if old.level != level:
            self._notify_change(old, self._state)

    def reset(self) -> None:
        """Reset to focused state."""
        old = self._state
        self._state = AttentionState(level=AttentionLevel.FOCUSED, reason="Reset")
        if old.level != AttentionLevel.FOCUSED:
            self._notify_change(old, self._state)

    def _on_signal(self, signal: SomaticSignal) -> None:
        """Handle incoming signal and recalculate attention."""
        recent = self.bus.recent(seconds=self._signal_window)
        new_level = self._calculate_level(recent)

        if new_level != self._state.level:
            old = self._state
            reason = self._derive_reason(recent, new_level)
            self._state = AttentionState(
                level=new_level,
                reason=reason,
                active_signals=len(recent),
                critical_signals=sum(1 for s in recent if s.is_critical),
            )
            self._notify_change(old, self._state)
        else:
            self._state.active_signals = len(recent)
            self._state.critical_signals = sum(1 for s in recent if s.is_critical)

    def _calculate_level(self, recent_signals: list[SomaticSignal]) -> AttentionLevel:
        """Calculate attention level from recent signals."""
        if not recent_signals:
            return AttentionLevel.FOCUSED

        critical_count = sum(1 for s in recent_signals if s.urgency >= SignalUrgency.CRITICAL)
        high_count = sum(1 for s in recent_signals if s.urgency >= SignalUrgency.HIGH)
        pressure_count = sum(1 for s in recent_signals if s.type == SignalType.PRESSURE)
        pain_count = sum(1 for s in recent_signals if s.type == SignalType.PAIN)

        if critical_count >= 3 or (critical_count >= 1 and pain_count >= 2):
            return AttentionLevel.OVERWHELMED
        elif critical_count >= 1 or high_count >= 3 or (pressure_count >= 3 and pain_count >= 1):
            return AttentionLevel.STRESSED
        elif high_count >= 1 or pressure_count >= 2 or pain_count >= 1:
            return AttentionLevel.ALERT
        else:
            return AttentionLevel.FOCUSED

    def _derive_reason(self, signals: list[SomaticSignal], level: AttentionLevel) -> str:
        """Generate human-readable reason for attention level."""
        if not signals:
            return "No active signals"

        type_counts: dict[str, int] = {}
        for s in signals:
            type_counts[s.type.value] = type_counts.get(s.type.value, 0) + 1

        dominant = max(type_counts, key=type_counts.get)
        recent_critical = [s for s in signals if s.is_critical]

        if recent_critical:
            return f"{level.label}: {recent_critical[-1].message}"
        return f"{level.label}: {type_counts[dominant]} {dominant} signals in {self._signal_window}s window"

    def _notify_change(self, old: AttentionState, new: AttentionState) -> None:
        """Notify all callbacks of attention level change."""
        for callback in self._callbacks:
            try:
                callback(old, new)
            except Exception:
                pass

    def get_recommendations(self) -> list[str]:
        """Get actionable recommendations based on current attention."""
        state = self._state
        recs: list[str] = []

        if state.level >= AttentionLevel.STRESSED:
            recs.append(f"Reduce task concurrency to {state.max_concurrency}")
            recs.append(f"Apply context budget ratio: {state.context_budget_ratio:.0%}")
        if state.level >= AttentionLevel.ALERT:
            recs.append(f"Increase governance sensitivity: {state.governance_sensitivity:.1f}x")
        if state.should_pause_non_critical:
            recs.append("PAUSE all non-critical tasks")
        if state.should_notify_operator:
            recs.append("NOTIFY operator of degraded state")

        return recs
