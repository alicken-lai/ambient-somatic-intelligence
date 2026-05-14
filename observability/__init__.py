"""
Observability Layer — Full-stack visibility for the Ambient OS cognitive runtime.

Provides comprehensive observability across all subsystems:

  tracer.py              — Distributed execution tracing with spans
  metrics_collector.py   — Aggregated metrics (token, memory, governance, somatic)
  telemetry.py           — Agent-level telemetry and execution profiling
  dashboard.py           — Status dashboard with ASCII visualization
  agent_decision_log.py  — Structured agent decision audit trail
  system_report.py       — Unified system health report (all subsystems)
  trace_schema.py        — Formal trace event schema definitions and validation

Design principles:
  - Zero-cost when disabled (lazy evaluation)
  - Structured output (JSON-lines compatible)
  - Cross-layer correlation (trace_id links execution→memory→governance)
  - Non-blocking (never delays the critical path)
"""

from observability.tracer import ExecutionTracer, Span, SpanKind
from observability.metrics_collector import MetricsCollector, MetricType
from observability.telemetry import AgentTelemetry
from observability.dashboard import Dashboard
from observability.agent_decision_log import AgentDecisionLog
from observability.system_report import SystemReport
from observability.trace_schema import TraceEventSchema, TraceEventType

__all__ = [
    "ExecutionTracer",
    "Span",
    "SpanKind",
    "MetricsCollector",
    "MetricType",
    "AgentTelemetry",
    "Dashboard",
    "AgentDecisionLog",
    "SystemReport",
    "TraceEventSchema",
    "TraceEventType",
]
