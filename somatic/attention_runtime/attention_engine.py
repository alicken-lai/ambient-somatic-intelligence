"""
Attention Weighting Engine — Multi-factor attention weight computation.

Extends the existing AttentionManager with richer weight computation
that considers signal severity, historical patterns, system stress,
governance escalation state, and memory pressure. Backward-compatible
with AttentionManager — uses it internally for state management.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from somatic.signal_bus import SomaticSignalBus, SomaticSignal, SignalType, SignalUrgency
from somatic.attention_manager import AttentionManager, AttentionLevel

logger = logging.getLogger(__name__)


@dataclass
class AttentionProfile:
    """Rich attention state with explanations for each weight."""
    weights: dict[str, float]
    dominant_signal: str
    stress_level: float
    explanation: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "weights": {k: round(v, 4) for k, v in self.weights.items()},
            "dominant_signal": self.dominant_signal,
            "stress_level": round(self.stress_level, 4),
            "explanation": self.explanation,
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
        }


class AttentionWeightingEngine:
    """
    Computes attention weights from multiple factors, building on
    the existing AttentionManager for state tracking.

    Usage:
        bus = SomaticSignalBus()
        attention_mgr = AttentionManager(bus)
        engine = AttentionWeightingEngine(attention_mgr, bus)

        weights = engine.compute_weights(signals, context)
        profile = engine.get_attention_profile()
    """

    BASE_WEIGHTS: dict[str, float] = {
        SignalType.PRESSURE.value: 0.20,
        SignalType.PAIN.value: 0.25,
        SignalType.FATIGUE.value: 0.15,
        SignalType.ALERTNESS.value: 0.15,
        SignalType.CALM.value: 0.10,
        SignalType.REFLEX.value: 0.15,
    }

    URGENCY_MULTIPLIERS: dict[int, float] = {
        SignalUrgency.LOW.value: 0.5,
        SignalUrgency.MEDIUM.value: 1.0,
        SignalUrgency.HIGH.value: 1.5,
        SignalUrgency.CRITICAL.value: 2.0,
        SignalUrgency.EMERGENCY.value: 3.0,
    }

    def __init__(
        self,
        attention_manager: AttentionManager,
        bus: SomaticSignalBus,
        history_window: float = 300.0,
    ):
        self._attention = attention_manager
        self._bus = bus
        self._history_window = history_window
        self._last_profile: AttentionProfile | None = None
        self._weight_history: list[dict[str, float]] = []
        self._max_weight_history = 100
        self._governance_escalation_level: float = 0.0
        self._memory_pressure: float = 0.0

    def set_governance_escalation(self, level: float) -> None:
        """Set governance escalation state (0.0 = calm, 1.0 = full escalation)."""
        self._governance_escalation_level = max(0.0, min(1.0, level))

    def set_memory_pressure(self, pressure: float) -> None:
        """Set memory pressure level (0.0 = no pressure, 1.0 = critical)."""
        self._memory_pressure = max(0.0, min(1.0, pressure))

    def compute_weights(
        self,
        signals: list[SomaticSignal],
        context: dict[str, Any] | None = None,
    ) -> dict[str, float]:
        """
        Compute attention weights considering multiple factors:
          - Signal severity and type distribution
          - Historical attention patterns
          - Current system stress level
          - Governance escalation state
          - Memory pressure
        """
        ctx = context or {}
        weights = dict(self.BASE_WEIGHTS)

        self._apply_signal_severity(weights, signals)
        self._apply_historical_patterns(weights)
        self._apply_stress_adjustment(weights)
        self._apply_governance_adjustment(weights)
        self._apply_memory_pressure(weights)

        self._normalize_weights(weights)

        self._weight_history.append(dict(weights))
        if len(self._weight_history) > self._max_weight_history:
            self._weight_history = self._weight_history[-self._max_weight_history:]

        dominant = max(weights, key=weights.get) if weights else "calm"
        stress = self._compute_stress_from_weights(weights)

        self._last_profile = AttentionProfile(
            weights=weights,
            dominant_signal=dominant,
            stress_level=stress,
            explanation=self._build_explanation(weights, signals, stress),
        )

        return weights

    def get_attention_profile(self) -> AttentionProfile:
        """Get the current attention profile with explanations."""
        if self._last_profile:
            return self._last_profile

        recent = self._bus.recent(seconds=self._history_window)
        self.compute_weights(recent)
        return self._last_profile  # type: ignore[return-value]

    def _apply_signal_severity(
        self,
        weights: dict[str, float],
        signals: list[SomaticSignal],
    ) -> None:
        """Adjust weights based on signal severity distribution."""
        if not signals:
            return

        type_severity: dict[str, float] = {}
        type_count: dict[str, int] = {}

        for signal in signals:
            key = signal.type.value
            multiplier = self.URGENCY_MULTIPLIERS.get(signal.urgency.value, 1.0)
            type_severity[key] = type_severity.get(key, 0.0) + multiplier
            type_count[key] = type_count.get(key, 0) + 1

        max_severity = max(type_severity.values()) if type_severity else 1.0
        for sig_type, severity in type_severity.items():
            boost = (severity / max(max_severity, 1.0)) * 0.3
            weights[sig_type] = weights.get(sig_type, 0.1) + boost

    def _apply_historical_patterns(self, weights: dict[str, float]) -> None:
        """Smooth weights using historical patterns (momentum)."""
        if len(self._weight_history) < 3:
            return

        recent = self._weight_history[-5:]
        for key in weights:
            historical_avg = sum(h.get(key, 0) for h in recent) / len(recent)
            weights[key] = weights[key] * 0.7 + historical_avg * 0.3

    def _apply_stress_adjustment(self, weights: dict[str, float]) -> None:
        """Under stress, amplify PAIN and PRESSURE weights."""
        state = self._attention.current_state()
        if state.level >= AttentionLevel.STRESSED:
            stress_factor = 1.0 + (int(state.level) - 1) * 0.15
            weights[SignalType.PAIN.value] *= stress_factor
            weights[SignalType.PRESSURE.value] *= stress_factor

    def _apply_governance_adjustment(self, weights: dict[str, float]) -> None:
        """Governance escalation increases ALERTNESS attention."""
        if self._governance_escalation_level > 0.1:
            weights[SignalType.ALERTNESS.value] *= (
                1.0 + self._governance_escalation_level * 0.5
            )
            weights[SignalType.REFLEX.value] *= (
                1.0 + self._governance_escalation_level * 0.3
            )

    def _apply_memory_pressure(self, weights: dict[str, float]) -> None:
        """Memory pressure increases PRESSURE and FATIGUE weights."""
        if self._memory_pressure > 0.1:
            weights[SignalType.PRESSURE.value] *= (
                1.0 + self._memory_pressure * 0.4
            )
            weights[SignalType.FATIGUE.value] *= (
                1.0 + self._memory_pressure * 0.3
            )

    @staticmethod
    def _normalize_weights(weights: dict[str, float]) -> None:
        """Normalize weights to sum to 1.0."""
        total = sum(weights.values())
        if total > 0:
            for key in weights:
                weights[key] /= total

    def _compute_stress_from_weights(self, weights: dict[str, float]) -> float:
        """Derive a stress level from current weight distribution."""
        stress_signals = (
            weights.get(SignalType.PAIN.value, 0)
            + weights.get(SignalType.PRESSURE.value, 0)
        )
        calm_signal = weights.get(SignalType.CALM.value, 0)
        return max(0.0, min(1.0, stress_signals - calm_signal))

    def _build_explanation(
        self,
        weights: dict[str, float],
        signals: list[SomaticSignal],
        stress: float,
    ) -> str:
        """Build human-readable explanation of current attention state."""
        dominant = max(weights, key=weights.get) if weights else "none"
        parts = [f"Dominant: {dominant} ({weights.get(dominant, 0):.0%})"]

        if stress > 0.6:
            parts.append(f"HIGH stress ({stress:.0%})")
        elif stress > 0.3:
            parts.append(f"moderate stress ({stress:.0%})")
        else:
            parts.append(f"low stress ({stress:.0%})")

        if self._governance_escalation_level > 0.1:
            parts.append(f"governance escalation {self._governance_escalation_level:.0%}")
        if self._memory_pressure > 0.1:
            parts.append(f"memory pressure {self._memory_pressure:.0%}")

        return " | ".join(parts)
