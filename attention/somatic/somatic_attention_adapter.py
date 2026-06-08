"""
Somatic attention adapter — bridges legacy somatic signals into the kernel.

The somatic subsystem emits :class:`attention.attention_state.AttentionSignal`
objects.  This adapter converts them into :class:`AttentionTarget` objects for
the attention kernel, annotating each with a ``somatic_severity`` that blends
the raw signal value with the current aggregate somatic stress.
"""

from __future__ import annotations

from attention.attention_state import AttentionSignal
from attention.core.attention_target import AttentionTarget


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class SomaticAttentionAdapter:
    """Converts legacy somatic signals into attention targets."""

    def __init__(self) -> None:
        self._stress: float = 0.0

    def update_stress(self, stress: float) -> None:
        """Set the current aggregate somatic stress level (0.0-1.0)."""
        self._stress = _clamp_unit(stress)

    @property
    def stress(self) -> float:
        return self._stress

    def from_signal(self, signal: AttentionSignal) -> AttentionTarget:
        """Convert *signal* into an :class:`AttentionTarget` with severity."""
        severity = _clamp_unit(signal.raw_value * (0.5 + 0.5 * self._stress))
        metadata = dict(signal.metadata)
        metadata.update(
            {
                "somatic_severity": severity,
                "somatic_stress": self._stress,
                "urgency": severity,
            }
        )
        return AttentionTarget(
            source_domain=signal.source_domain,
            signal_type=signal.signal_type,
            raw_value=signal.raw_value,
            metadata=metadata,
            source_ref=signal.signal_id,
        )
