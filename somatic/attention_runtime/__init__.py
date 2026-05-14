"""
Somatic Attention Runtime — Phase F of Ambient OS v0.3.

Advanced attention processing pipeline that builds on the existing
somatic subsystem. Composes signal normalization, anomaly amplification,
priority-based filtering, stress scoring, and adaptive throttling into
a unified runtime.

Components:
  attention_engine.py   — Multi-factor attention weighting
  anomaly_amplifier.py  — Context-aware anomaly signal amplification
  signal_prioritizer.py — Priority queue for signal processing
  execution_throttle.py — Adaptive execution throttling
  stress_scorer.py      — Runtime stress scoring from multiple sources
  attention_runtime.py  — Unified runtime composing all components
"""

from somatic.attention_runtime.attention_engine import AttentionWeightingEngine, AttentionProfile
from somatic.attention_runtime.anomaly_amplifier import AnomalyAmplifier, AmplifiedSignal
from somatic.attention_runtime.signal_prioritizer import SignalPrioritizer, PrioritizedSignal
from somatic.attention_runtime.execution_throttle import AdaptiveExecutionThrottle, ThrottleState, ThrottleLevel
from somatic.attention_runtime.stress_scorer import RuntimeStressScorer, StressScore, StressMap, StressLevel
from somatic.attention_runtime.attention_runtime import SomaticAttentionRuntime, AnomalyEscalationReport

__all__ = [
    "AttentionWeightingEngine",
    "AttentionProfile",
    "AnomalyAmplifier",
    "AmplifiedSignal",
    "SignalPrioritizer",
    "PrioritizedSignal",
    "AdaptiveExecutionThrottle",
    "ThrottleState",
    "ThrottleLevel",
    "RuntimeStressScorer",
    "StressScore",
    "StressMap",
    "StressLevel",
    "SomaticAttentionRuntime",
    "AnomalyEscalationReport",
]
