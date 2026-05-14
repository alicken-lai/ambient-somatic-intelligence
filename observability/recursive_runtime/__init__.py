"""
Recursive Runtime Observability — Phase G of Ambient OS Architecture.

Meta-cognitive observability: the system observing its own thought processes.

  cognition_tracer.py        — Trace cognitive decisions (routing, retrieval, etc.)
  memory_flow_tracer.py      — Trace memory operations and data flow
  context_assembly_tracer.py — Trace context assembly efficiency
  governance_analytics.py    — Governance system load and effectiveness analytics
  recursive_telemetry.py     — Observability observing itself (overhead, health)
  introspection_dashboard.py — Unified introspection visualization

Design principles:
  - Lightweight: Must not significantly increase system overhead
  - Structured: All output is JSON-serializable via to_dict()
  - Non-blocking: Never delays the critical path
  - Self-aware: Can detect when observation itself becomes a burden
"""

from observability.recursive_runtime.cognition_tracer import (
    CognitionTracer,
    CognitionTrace,
    ReasoningChain,
    ReasoningStep,
    DecisionType,
)
from observability.recursive_runtime.memory_flow_tracer import (
    MemoryFlowTracer,
    MemoryFlowSummary,
    RecallEvent,
    StoreEvent,
    CompressionEvent,
)
from observability.recursive_runtime.context_assembly_tracer import (
    ContextAssemblyTracer,
    AssemblyReport,
    AssemblyEvent,
    RetrievalEvent,
)
from observability.recursive_runtime.governance_analytics import (
    GovernanceLoadAnalytics,
    GovernanceLoadReport,
    GovernanceEffectivenessReport,
)
from observability.recursive_runtime.recursive_telemetry import (
    RecursiveTelemetry,
    RecursiveTelemetryReport,
    TracerHealth,
    MetricsHealth,
)
from observability.recursive_runtime.introspection_dashboard import (
    IntrospectionDashboard,
)

__all__ = [
    # Cognition Tracer
    "CognitionTracer",
    "CognitionTrace",
    "ReasoningChain",
    "ReasoningStep",
    "DecisionType",
    # Memory Flow Tracer
    "MemoryFlowTracer",
    "MemoryFlowSummary",
    "RecallEvent",
    "StoreEvent",
    "CompressionEvent",
    # Context Assembly Tracer
    "ContextAssemblyTracer",
    "AssemblyReport",
    "AssemblyEvent",
    "RetrievalEvent",
    # Governance Analytics
    "GovernanceLoadAnalytics",
    "GovernanceLoadReport",
    "GovernanceEffectivenessReport",
    # Recursive Telemetry
    "RecursiveTelemetry",
    "RecursiveTelemetryReport",
    "TracerHealth",
    "MetricsHealth",
    # Introspection Dashboard
    "IntrospectionDashboard",
]
