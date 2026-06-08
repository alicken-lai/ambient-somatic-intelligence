"""
Somatic runtime bridge — accepts raw payloads from the somatic subsystem.

Converts loosely-typed payload dicts (``{"severity": ..., "stress": ...}``)
into :class:`AttentionSignal` objects and submits them through a
:class:`RuntimeSomaticAttention` instance.
"""

from __future__ import annotations

from typing import Any

from attention.attention_state import AttentionSignal
from attention.somatic.runtime_somatic_attention import RuntimeSomaticAttention


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class SomaticRuntimeBridge:
    """Bridges raw somatic payloads into the runtime somatic submission path."""

    def __init__(self, runtime: RuntimeSomaticAttention) -> None:
        self.runtime = runtime

    def from_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        severity = _clamp_unit(payload.get("severity", 0.0))
        stress = _clamp_unit(payload.get("stress", 0.0))
        signal_type = str(payload.get("signal_type", "somatic_payload"))
        self.runtime.set_stress(stress)
        signal = AttentionSignal(
            source_domain="somatic",
            signal_type=signal_type,
            raw_value=severity,
            metadata={"source": "payload"},
        )
        return self.runtime.submit_signal(signal)
