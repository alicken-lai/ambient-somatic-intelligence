"""
Cognitive Entropy Controller — runtime dimension scoring (legacy).

**SSOT (v0.4.2+):** `kernel.entropy.EntropyController` is the canonical entropy
layer for truth/patch/coupling observability. This package remains for context
compression, damping, and load regulation — not kernel stabilization metrics.

Components:
  entropy_scorer.py       — Composite entropy scoring across all system dimensions
  damping_mechanism.py    — Automatic damping actions triggered by entropy thresholds
  load_regulator.py       — Global rate limiting and backpressure at queue boundaries
  decay_enforcer.py       — Scheduled enforcement of memory decay, TTL sweeps, rotation
  compression_triggers.py — Entropy-aware context compression recommendations
"""

from kernel.entropy import EntropyController as KernelEntropyController

from runtime.entropy_controller.entropy_scorer import (
    EntropyScorer,
    EntropyScore,
    DimensionScore,
)
from runtime.entropy_controller.damping_mechanism import (
    DampingMechanism,
    DampingConfig,
    DampingAction,
    DampingResult,
)
from runtime.entropy_controller.load_regulator import (
    LoadRegulator,
    LoadConfig,
    RateCheckResult,
    PressureResult,
    ThrottleRecommendation,
)
from runtime.entropy_controller.decay_enforcer import (
    DecayEnforcer,
    DecayConfig,
    DecayTarget,
    DecayAssessment,
    DecayResult,
)
from runtime.entropy_controller.compression_triggers import (
    CompressionTriggers,
    CompressionConfig,
    CompressionRecommendation,
    ContextReductionPlan,
    OcrBloatReport,
)

__all__ = [
    "KernelEntropyController",
    "EntropyScorer",
    "EntropyScore",
    "DimensionScore",
    "DampingMechanism",
    "DampingConfig",
    "DampingAction",
    "DampingResult",
    "LoadRegulator",
    "LoadConfig",
    "RateCheckResult",
    "PressureResult",
    "ThrottleRecommendation",
    "DecayEnforcer",
    "DecayConfig",
    "DecayTarget",
    "DecayAssessment",
    "DecayResult",
    "CompressionTriggers",
    "CompressionConfig",
    "CompressionRecommendation",
    "ContextReductionPlan",
    "OcrBloatReport",
]
