"""attention.runtime — runtime wiring of the attention layer.

Telemetry ingestion, pressure/budget/recovery control, bounded memory
activation, and the kernel-to-memory consolidation bridge.  Governed activation
(v0.6.0+) and calibrated activation (v0.5.4) remain to be rebuilt.
"""

from attention.runtime.attention_pressure_controller import (
    AttentionPressureController,
    PressureDecision,
    PressureSnapshot,
)
from attention.runtime.calibrated_attention_activation import (
    CalibratedAttentionActivation,
)
from attention.runtime.confidence_weighted_salience import (
    ConfidenceWeightedSalience,
    WeightedSalience,
)
from attention.runtime.overload_recovery import OverloadRecovery
from attention.runtime.precursor_memory_bridge import PrecursorMemoryBridge
from attention.runtime.runtime_attention_budget import RuntimeAttentionBudget
from attention.runtime.runtime_attention_memory_bridge import (
    RuntimeAttentionMemoryBridge,
)
from attention.runtime.runtime_memory_activation import RuntimeMemoryActivation
from attention.runtime.telemetry_attention_adapter import TelemetryAttentionAdapter
from attention.runtime.telemetry_attention_signal import telemetry_to_target

__all__ = [
    "AttentionPressureController",
    "PressureDecision",
    "PressureSnapshot",
    "CalibratedAttentionActivation",
    "ConfidenceWeightedSalience",
    "WeightedSalience",
    "OverloadRecovery",
    "PrecursorMemoryBridge",
    "RuntimeAttentionBudget",
    "RuntimeAttentionMemoryBridge",
    "RuntimeMemoryActivation",
    "TelemetryAttentionAdapter",
    "telemetry_to_target",
]
