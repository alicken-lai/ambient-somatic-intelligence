"""
Cognitive Trace v2 — Causal tracing system for Ambient OS.

Upgrades observability from subsystem-specific traces to a unified causal
model where every action is replayable and every decision has provenance.

Modules:
    causal_trace_schema     — Unified event model (CausalEvent, CausalChain)
    execution_lineage       — Full execution lineage tracking
    decision_provenance     — Decision reasoning reconstruction
    memory_injection_tracer — Memory injection effectiveness tracking
    replay_engine           — Execution replay planning and trace diffing
"""

from observability.cognitive_trace_v2.causal_trace_schema import (
    CausalChain,
    CausalEvent,
    CausalEventType,
    TraceSession,
)
from observability.cognitive_trace_v2.decision_provenance import (
    DecisionProvenanceTracker,
    DecisionProvenance,
    DecisionRecord,
    ReasoningPath,
    ReasoningStep,
)
from observability.cognitive_trace_v2.execution_lineage import (
    ExecutionLineageTracer,
    LineageConfig,
)
from observability.cognitive_trace_v2.memory_injection_tracer import (
    EffectivenessReport,
    InfluenceMap,
    InjectedMemory,
    InjectionAnomaly,
    InjectionOutcome,
    InjectionRecord,
    InjectionTraceConfig,
    MemoryInjectionTracer,
)
from observability.cognitive_trace_v2.replay_engine import (
    ExecutionDiff,
    ReplayEngine,
    ReplayPlan,
    ReplaySnapshot,
    ReplayStep,
    ReplayValidation,
)

__all__ = [
    "CausalChain",
    "CausalEvent",
    "CausalEventType",
    "TraceSession",
    "ExecutionLineageTracer",
    "LineageConfig",
    "DecisionProvenanceTracker",
    "DecisionProvenance",
    "DecisionRecord",
    "ReasoningPath",
    "ReasoningStep",
    "MemoryInjectionTracer",
    "InjectionTraceConfig",
    "InjectedMemory",
    "InjectionRecord",
    "InjectionOutcome",
    "EffectivenessReport",
    "InfluenceMap",
    "InjectionAnomaly",
    "ReplayEngine",
    "ReplaySnapshot",
    "ReplayPlan",
    "ReplayStep",
    "ReplayValidation",
    "ExecutionDiff",
]
