"""
Attention Architecture — Formal attention layer for Ambient OS.

Provides unified cross-domain salience scoring, novelty / weak-signal
detection, finite attention budgeting, and governance-integrated
escalation routing.

This layer builds *on top of* the existing somatic attention subsystem
(``somatic.attention_manager``, ``somatic.attention_runtime``) and extends
it with:

  - Domain-agnostic ``AttentionSignal`` representation
  - Configurable multi-factor ``SalienceEngine``
  - Habituation-aware ``NoveltyDetector``
  - Below-threshold ``WeakSignalDetector`` for emerging patterns
  - Finite-resource ``PriorityAllocator`` with ``AttentionBudget``
  - Governance-integrated ``EscalationRouter``
"""

from __future__ import annotations

from attention.attention_state import (
    AttentionSignal,
    AttentionSnapshot,
    TemporalContext,
    OperationalPhase,
    DayPhase,
)
from attention.salience_engine import SalienceEngine, SalienceScore
from attention.novelty_detector import NoveltyDetector, NoveltyScore
from attention.weak_signal_detector import (
    WeakSignalDetector,
    EmergingPattern,
    Trend,
)
from attention.priority_allocator import (
    PriorityAllocator,
    AttentionBudget,
    AllocationResult,
    AllocationEntry,
)
from attention.escalation_router import (
    EscalationRouter,
    EscalationDecision,
    EscalationAction,
)
from attention.kernel.attention_kernel import AttentionKernel, KernelTickResult
from attention.kernel.salience_engine import KernelSalienceEngine

__all__ = [
    # attention_state
    "AttentionSignal",
    "AttentionSnapshot",
    "TemporalContext",
    "OperationalPhase",
    "DayPhase",
    # salience_engine
    "SalienceEngine",
    "SalienceScore",
    # novelty_detector
    "NoveltyDetector",
    "NoveltyScore",
    # weak_signal_detector
    "WeakSignalDetector",
    "EmergingPattern",
    "Trend",
    # priority_allocator
    "PriorityAllocator",
    "AttentionBudget",
    "AllocationResult",
    "AllocationEntry",
    # escalation_router
    "EscalationRouter",
    "EscalationDecision",
    "EscalationAction",
    # kernel (v0.5 layered architecture)
    "AttentionKernel",
    "KernelTickResult",
    "KernelSalienceEngine",
]
