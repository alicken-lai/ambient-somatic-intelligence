"""
Anomaly Amplifier — Context-aware severity amplification for anomaly signals.

Adjusts signal severity based on contextual factors:
  - Correlation with other recent signals (compound patterns)
  - System stress level (amplify more when already stressed)
  - Historical frequency (novel anomalies get higher amplification)
  - Governance sensitivity level

Amplification is bounded: max 3x original severity, capped at 1.0.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from somatic.signal_bus import SomaticSignalBus, SomaticSignal, SignalType

logger = logging.getLogger(__name__)


MAX_AMPLIFICATION_FACTOR = 3.0
MAX_SEVERITY = 1.0


@dataclass
class AmplifiedSignal:
    """A signal with amplified severity and explanation."""
    original_signal: SomaticSignal
    amplified_severity: float
    amplification_factor: float
    reason: str
    factors: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_type": self.original_signal.type.value,
            "original_urgency": self.original_signal.urgency.value,
            "original_source": self.original_signal.source,
            "amplified_severity": round(self.amplified_severity, 4),
            "amplification_factor": round(self.amplification_factor, 4),
            "reason": self.reason,
            "factors": {k: round(v, 4) for k, v in self.factors.items()},
        }


class AnomalyAmplifier:
    """
    Amplifies anomaly signals based on multi-factor context.

    Usage:
        bus = SomaticSignalBus()
        amplifier = AnomalyAmplifier(bus)

        result = amplifier.amplify(signal, context={"stress_level": 0.7})
        print(result.amplified_severity, result.reason)
    """

    def __init__(
        self,
        bus: SomaticSignalBus,
        correlation_window: float = 60.0,
        novelty_window: float = 600.0,
    ):
        self._bus = bus
        self._correlation_window = correlation_window
        self._novelty_window = novelty_window
        self._historical_counts: dict[str, int] = defaultdict(int)
        self._governance_sensitivity: float = 1.0

    def set_governance_sensitivity(self, sensitivity: float) -> None:
        """Set governance sensitivity multiplier (1.0 = normal)."""
        self._governance_sensitivity = max(0.5, min(3.0, sensitivity))

    def amplify(
        self,
        signal: SomaticSignal,
        context: dict[str, Any] | None = None,
    ) -> AmplifiedSignal:
        """
        Amplify a signal's severity based on contextual factors.

        The amplified severity is bounded by MAX_AMPLIFICATION_FACTOR (3x)
        and capped at MAX_SEVERITY (1.0).
        """
        ctx = context or {}
        base_severity = signal.value if signal.value > 0 else (
            signal.urgency.value / 5.0
        )
        base_severity = min(base_severity, 1.0)

        sig_key = f"{signal.type.value}:{signal.source}"
        self._historical_counts[sig_key] += 1

        correlation_factor = self._correlation_boost(signal)
        stress_factor = self._stress_boost(ctx.get("stress_level", 0.0))
        novelty_factor = self._novelty_boost(sig_key)
        governance_factor = self._governance_boost()

        total_factor = (
            1.0
            + correlation_factor
            + stress_factor
            + novelty_factor
            + governance_factor
        )

        total_factor = min(total_factor, MAX_AMPLIFICATION_FACTOR)

        amplified = min(base_severity * total_factor, MAX_SEVERITY)

        factors = {
            "correlation": correlation_factor,
            "stress": stress_factor,
            "novelty": novelty_factor,
            "governance": governance_factor,
        }

        reason = self._build_reason(factors, total_factor)

        logger.debug(
            "Amplified %s from %.3f to %.3f (factor=%.2f): %s",
            signal.type.value, base_severity, amplified, total_factor, reason,
        )

        return AmplifiedSignal(
            original_signal=signal,
            amplified_severity=amplified,
            amplification_factor=total_factor,
            reason=reason,
            factors=factors,
        )

    def _correlation_boost(self, signal: SomaticSignal) -> float:
        """Boost severity when correlated signals are present."""
        recent = self._bus.recent(seconds=self._correlation_window)
        if len(recent) < 2:
            return 0.0

        correlated_types = {
            SignalType.PRESSURE: [SignalType.PAIN, SignalType.FATIGUE],
            SignalType.PAIN: [SignalType.PRESSURE, SignalType.ALERTNESS],
            SignalType.FATIGUE: [SignalType.PRESSURE],
            SignalType.ALERTNESS: [SignalType.PAIN],
        }

        related = correlated_types.get(signal.type, [])
        related_count = sum(
            1 for s in recent
            if s.type in related and s.source != signal.source
        )

        return min(related_count * 0.15, 0.6)

    def _stress_boost(self, stress_level: float) -> float:
        """Higher amplification when system is already stressed."""
        if stress_level < 0.3:
            return 0.0
        return min(stress_level * 0.5, 0.5)

    def _novelty_boost(self, signal_key: str) -> float:
        """Novel (rarely seen) anomalies get higher amplification."""
        count = self._historical_counts.get(signal_key, 0)
        if count <= 1:
            return 0.4
        elif count <= 3:
            return 0.2
        elif count <= 10:
            return 0.1
        return 0.0

    def _governance_boost(self) -> float:
        """Governance sensitivity increases amplification."""
        if self._governance_sensitivity <= 1.0:
            return 0.0
        return min((self._governance_sensitivity - 1.0) * 0.3, 0.4)

    @staticmethod
    def _build_reason(factors: dict[str, float], total_factor: float) -> str:
        """Build a human-readable amplification reason."""
        active = [k for k, v in factors.items() if v > 0.05]
        if not active:
            return "No amplification applied"

        parts = [f"{k}={v:.0%}" for k, v in factors.items() if v > 0.05]
        return f"Amplified {total_factor:.1f}x due to: {', '.join(parts)}"
