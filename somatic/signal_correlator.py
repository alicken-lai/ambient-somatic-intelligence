"""
Signal Correlator — Compound pattern detection across somatic signals.

Individual signals tell you what is happening; correlations tell you
what it MEANS. This module detects multi-signal patterns:

  PRESSURE + PAIN within 30s  → amplified "system distress"
  FATIGUE + PRESSURE           → "resource exhaustion cascade"
  PAIN spike + CALM drop       → "instability oscillation"

The correlator subscribes to the SignalBus, evaluates correlation
rules over recent signal windows, and emits synthesized signals
back onto the bus when compound patterns are detected.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from somatic.signal_bus import (
    SomaticSignalBus,
    SomaticSignal,
    SignalType,
    SignalUrgency,
)


@dataclass
class CorrelationRule:
    """Defines a compound pattern to detect across signal types."""
    name: str
    required_types: list[SignalType]
    min_urgency: SignalUrgency = SignalUrgency.MEDIUM
    window_seconds: float = 30.0
    cooldown_seconds: float = 60.0
    severity_multiplier: float = 1.5
    emit_type: SignalType = SignalType.ALERTNESS
    emit_urgency: SignalUrgency = SignalUrgency.HIGH
    description: str = ""
    last_triggered: float = 0.0

    @property
    def in_cooldown(self) -> bool:
        return (time.time() - self.last_triggered) < self.cooldown_seconds


@dataclass
class CorrelatedEvent:
    """A detected compound pattern."""
    rule_name: str
    matched_signals: list[SomaticSignal]
    severity_multiplier: float
    description: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "matched_signal_count": len(self.matched_signals),
            "matched_types": list({s.type.value for s in self.matched_signals}),
            "severity_multiplier": self.severity_multiplier,
            "description": self.description,
            "timestamp": self.timestamp,
        }


BUILTIN_CORRELATION_RULES: list[CorrelationRule] = [
    CorrelationRule(
        name="system_distress",
        required_types=[SignalType.PRESSURE, SignalType.PAIN],
        min_urgency=SignalUrgency.MEDIUM,
        window_seconds=30.0,
        cooldown_seconds=120.0,
        severity_multiplier=1.5,
        emit_type=SignalType.ALERTNESS,
        emit_urgency=SignalUrgency.CRITICAL,
        description="Concurrent resource pressure and errors indicate system distress",
    ),
    CorrelationRule(
        name="resource_exhaustion_cascade",
        required_types=[SignalType.FATIGUE, SignalType.PRESSURE],
        min_urgency=SignalUrgency.MEDIUM,
        window_seconds=60.0,
        cooldown_seconds=180.0,
        severity_multiplier=1.8,
        emit_type=SignalType.ALERTNESS,
        emit_urgency=SignalUrgency.CRITICAL,
        description="Prolonged fatigue combined with pressure signals exhaustion cascade",
    ),
    CorrelationRule(
        name="multi_source_pressure",
        required_types=[SignalType.PRESSURE, SignalType.PRESSURE],
        min_urgency=SignalUrgency.MEDIUM,
        window_seconds=30.0,
        cooldown_seconds=60.0,
        severity_multiplier=1.3,
        emit_type=SignalType.PRESSURE,
        emit_urgency=SignalUrgency.HIGH,
        description="Pressure from multiple sources simultaneously",
    ),
    CorrelationRule(
        name="error_storm",
        required_types=[SignalType.PAIN, SignalType.PAIN],
        min_urgency=SignalUrgency.MEDIUM,
        window_seconds=20.0,
        cooldown_seconds=60.0,
        severity_multiplier=2.0,
        emit_type=SignalType.REFLEX,
        emit_urgency=SignalUrgency.CRITICAL,
        description="Multiple pain signals in rapid succession indicate error storm",
    ),
]


CorrelationCallback = Callable[[CorrelatedEvent], None]


class SignalCorrelator:
    """
    Detects compound signal patterns and emits synthesized signals.

    Usage:
        bus = SomaticSignalBus()
        correlator = SignalCorrelator(bus)

        # The correlator auto-subscribes and emits when patterns match
        bus.emit_pressure("cpu", "CPU high", 90.0, 70.0)
        bus.emit_pain("disk", "Write failure")
        # → correlator detects "system_distress" and emits ALERTNESS/CRITICAL
    """

    def __init__(
        self,
        bus: SomaticSignalBus | None = None,
        rules: list[CorrelationRule] | None = None,
    ):
        self.bus = bus or SomaticSignalBus()
        self.rules = rules or [
            CorrelationRule(**r.__dict__) for r in BUILTIN_CORRELATION_RULES
        ]
        self._callbacks: list[CorrelationCallback] = []
        self._history: list[CorrelatedEvent] = []
        self._max_history = 100
        self._subscribed = False

    def subscribe(self) -> None:
        """Subscribe to the bus for correlation evaluation."""
        if not self._subscribed:
            self.bus.on_any(self._on_signal)
            self._subscribed = True

    def on_correlation(self, callback: CorrelationCallback) -> None:
        """Register callback for correlated events."""
        self._callbacks.append(callback)

    def add_rule(self, rule: CorrelationRule) -> None:
        """Add a custom correlation rule."""
        self.rules.append(rule)

    def correlate(self, recent_signals: list[SomaticSignal]) -> list[CorrelatedEvent]:
        """
        Evaluate correlation rules against a list of signals.

        Returns detected correlated events without emitting to the bus.
        """
        events: list[CorrelatedEvent] = []

        for rule in self.rules:
            if rule.in_cooldown:
                continue

            matched = self._match_rule(rule, recent_signals)
            if matched:
                event = CorrelatedEvent(
                    rule_name=rule.name,
                    matched_signals=matched,
                    severity_multiplier=rule.severity_multiplier,
                    description=rule.description,
                )
                events.append(event)

        return events

    def recent_correlations(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent correlated events."""
        return [e.to_dict() for e in self._history[-limit:]]

    def status(self) -> dict[str, Any]:
        """Current correlator status."""
        return {
            "subscribed": self._subscribed,
            "rules_count": len(self.rules),
            "rules_in_cooldown": sum(1 for r in self.rules if r.in_cooldown),
            "total_correlations": len(self._history),
            "recent": self.recent_correlations(5),
        }

    def _on_signal(self, signal: SomaticSignal) -> None:
        """Handle incoming signal — evaluate all correlation rules."""
        recent = self.bus.recent(seconds=max(r.window_seconds for r in self.rules))
        events = self.correlate(recent)

        for event in events:
            rule = next(r for r in self.rules if r.name == event.rule_name)
            rule.last_triggered = time.time()

            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

            for cb in self._callbacks:
                try:
                    cb(event)
                except Exception:
                    pass

            self.bus.emit(SomaticSignal(
                type=rule.emit_type,
                urgency=rule.emit_urgency,
                source=f"correlator.{rule.name}",
                message=f"Correlation detected: {rule.description}",
                value=rule.severity_multiplier,
                metadata={"correlation": event.to_dict()},
            ))

    def _match_rule(
        self, rule: CorrelationRule, signals: list[SomaticSignal]
    ) -> list[SomaticSignal] | None:
        """
        Check if signals satisfy a correlation rule.

        For rules requiring the same type twice (e.g., PRESSURE+PRESSURE),
        we require signals from different sources.
        """
        cutoff = time.time() - rule.window_seconds
        qualifying = [
            s for s in signals
            if s.timestamp >= cutoff
            and s.urgency >= rule.min_urgency
            and not s.source.startswith("correlator.")
        ]

        type_counts: dict[SignalType, int] = {}
        for t in rule.required_types:
            type_counts[t] = type_counts.get(t, 0) + 1

        matched: list[SomaticSignal] = []
        used_sources: set[str] = set()

        for req_type, needed in type_counts.items():
            candidates = [
                s for s in qualifying
                if s.type == req_type and s.source not in used_sources
            ]

            if req_type in type_counts and type_counts[req_type] > 1:
                unique_sources = {s.source for s in candidates}
                if len(unique_sources) < needed:
                    return None
                seen: set[str] = set()
                for s in candidates:
                    if s.source not in seen and len(seen) < needed:
                        matched.append(s)
                        seen.add(s.source)
                        used_sources.add(s.source)
            else:
                if len(candidates) < needed:
                    return None
                matched.extend(candidates[:needed])
                for s in candidates[:needed]:
                    used_sources.add(s.source)

        return matched if matched else None
