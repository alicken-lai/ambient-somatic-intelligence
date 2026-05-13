"""
Anomaly Event Stream — Maps somatic signal patterns to cognitive responses.

The bridge between raw somatic signals and intelligent system responses:

  Signal Pattern          → Cognitive Response
  ─────────────────────────────────────────────
  high latency            → guardian attention increase
  memory pressure         → context compression trigger
  disk anomaly            → execution slowdown
  network instability     → retry policy adaptation
  sustained fatigue       → task graph throttling
  multiple pain signals   → incident declaration

This module completes the somatic→cognition loop by defining
response rules that connect the SignalBus to system actuators.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from somatic.signal_bus import SomaticSignalBus, SomaticSignal, SignalType, SignalUrgency
from somatic.attention_manager import AttentionManager, AttentionLevel


@dataclass
class CognitiveResponse:
    """A system response triggered by somatic patterns."""
    name: str
    action: str
    trigger_reason: str
    urgency: SignalUrgency
    parameters: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    executed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "action": self.action,
            "trigger_reason": self.trigger_reason,
            "urgency": self.urgency.value,
            "parameters": self.parameters,
            "timestamp": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "executed": self.executed,
        }


@dataclass
class ResponseRule:
    """A rule that maps signal patterns to cognitive responses."""
    name: str
    signal_type: SignalType | None = None  # None = any type
    min_urgency: SignalUrgency = SignalUrgency.MEDIUM
    min_count_in_window: int = 1
    window_seconds: float = 120.0
    cooldown_seconds: float = 300.0
    response_action: str = ""
    response_params: dict[str, Any] = field(default_factory=dict)
    last_triggered: float = 0.0

    @property
    def in_cooldown(self) -> bool:
        return (time.time() - self.last_triggered) < self.cooldown_seconds


BUILTIN_RULES: list[ResponseRule] = [
    ResponseRule(
        name="memory_pressure_compress",
        signal_type=SignalType.PRESSURE,
        min_urgency=SignalUrgency.HIGH,
        min_count_in_window=2,
        window_seconds=120,
        cooldown_seconds=300,
        response_action="context_compression",
        response_params={"target_ratio": 0.6, "priority": "scratchpad_first"},
    ),
    ResponseRule(
        name="fatigue_throttle",
        signal_type=SignalType.FATIGUE,
        min_urgency=SignalUrgency.MEDIUM,
        min_count_in_window=3,
        window_seconds=180,
        cooldown_seconds=600,
        response_action="scheduler_throttle",
        response_params={"max_concurrent": 2, "backoff_multiplier": 1.5},
    ),
    ResponseRule(
        name="pain_increase_governance",
        signal_type=SignalType.PAIN,
        min_urgency=SignalUrgency.MEDIUM,
        min_count_in_window=2,
        window_seconds=60,
        cooldown_seconds=180,
        response_action="governance_escalate",
        response_params={"sensitivity_multiplier": 1.5},
    ),
    ResponseRule(
        name="critical_pressure_emergency",
        signal_type=SignalType.PRESSURE,
        min_urgency=SignalUrgency.CRITICAL,
        min_count_in_window=1,
        window_seconds=60,
        cooldown_seconds=120,
        response_action="emergency_pause",
        response_params={"pause_non_critical": True, "notify_operator": True},
    ),
    ResponseRule(
        name="calm_restore_normal",
        signal_type=SignalType.CALM,
        min_urgency=SignalUrgency.LOW,
        min_count_in_window=3,
        window_seconds=300,
        cooldown_seconds=60,
        response_action="restore_normal",
        response_params={"reset_throttle": True, "reset_governance": True},
    ),
    ResponseRule(
        name="reflex_immediate_action",
        signal_type=SignalType.REFLEX,
        min_urgency=SignalUrgency.HIGH,
        min_count_in_window=1,
        window_seconds=10,
        cooldown_seconds=30,
        response_action="reflex_execute",
        response_params={"bypass_review": True},
    ),
]


ResponseCallback = Callable[[CognitiveResponse], None]


class AnomalyEventStream:
    """
    Processes somatic signal patterns and triggers cognitive responses.

    Usage:
        bus = SomaticSignalBus()
        attention = AttentionManager(bus)
        stream = AnomalyEventStream(bus, attention)

        # Register response handlers
        stream.on_response(handle_cognitive_response)

        # Signals flow through bus → stream evaluates → responses triggered
        bus.emit_pressure("memory", "Memory at 95%", 95.0, 85.0)
        bus.emit_pressure("memory", "Memory at 96%", 96.0, 85.0)
        # → triggers "memory_pressure_compress" response
    """

    def __init__(
        self,
        bus: SomaticSignalBus | None = None,
        attention: AttentionManager | None = None,
        rules: list[ResponseRule] | None = None,
    ):
        self.bus = bus or SomaticSignalBus()
        self.attention = attention or AttentionManager(self.bus)
        self.rules = rules or [ResponseRule(**r.__dict__) for r in BUILTIN_RULES]
        self._callbacks: list[ResponseCallback] = []
        self._response_history: list[CognitiveResponse] = []
        self._max_history = 100

        self.bus.on_any(self._evaluate_rules)

    def on_response(self, callback: ResponseCallback) -> None:
        """Register callback for cognitive responses."""
        self._callbacks.append(callback)

    def _evaluate_rules(self, signal: SomaticSignal) -> None:
        """Evaluate all rules against current signal state."""
        for rule in self.rules:
            if rule.in_cooldown:
                continue

            if rule.signal_type and signal.type != rule.signal_type:
                continue

            if signal.urgency < rule.min_urgency:
                continue

            matching = self.bus.recent(
                signal_type=rule.signal_type,
                seconds=rule.window_seconds,
            )
            qualifying = [s for s in matching if s.urgency >= rule.min_urgency]

            if len(qualifying) >= rule.min_count_in_window:
                self._trigger_response(rule, qualifying)

    def _trigger_response(self, rule: ResponseRule, signals: list[SomaticSignal]) -> None:
        """Trigger a cognitive response from a matched rule."""
        rule.last_triggered = time.time()

        response = CognitiveResponse(
            name=rule.name,
            action=rule.response_action,
            trigger_reason=f"Rule '{rule.name}': {len(signals)} signals in {rule.window_seconds}s",
            urgency=max(s.urgency for s in signals),
            parameters=dict(rule.response_params),
        )

        self._response_history.append(response)
        if len(self._response_history) > self._max_history:
            self._response_history = self._response_history[-self._max_history:]

        for callback in self._callbacks:
            try:
                callback(response)
                response.executed = True
            except Exception:
                pass

    def recent_responses(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent cognitive responses."""
        return [r.to_dict() for r in self._response_history[-limit:]]

    def status(self) -> dict[str, Any]:
        """Get stream status."""
        attention_state = self.attention.current_state()
        bus_state = self.bus.current_state()

        active_rules = [r.name for r in self.rules if not r.in_cooldown]
        cooldown_rules = [r.name for r in self.rules if r.in_cooldown]

        return {
            "attention_level": attention_state.level.label,
            "bus_signals_total": bus_state["total_signals"],
            "bus_signals_60s": bus_state["signals_last_60s"],
            "dominant_signal": bus_state["dominant_signal"],
            "rules_total": len(self.rules),
            "rules_active": len(active_rules),
            "rules_in_cooldown": cooldown_rules,
            "responses_triggered": len(self._response_history),
            "recommendations": self.attention.get_recommendations(),
        }

    def full_state(self) -> dict[str, Any]:
        """Get complete somatic system state."""
        return {
            "attention": self.attention.current_state().to_dict(),
            "bus": self.bus.current_state(),
            "stream": self.status(),
            "recent_responses": self.recent_responses(5),
        }
