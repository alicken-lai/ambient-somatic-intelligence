"""
Observability Layer — Phase 6 of Ambient OS Architecture Refactor.

Provides full-stack visibility into the cognitive operating system:

  tracer.py           — Distributed execution tracing with spans
  metrics_collector.py — Aggregated metrics (token, memory, governance, somatic)
  telemetry.py        — Agent-level telemetry and execution profiling
  dashboard.py        — Status dashboard with ASCII visualization

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

__all__ = [
    "ExecutionTracer",
    "Span",
    "SpanKind",
    "MetricsCollector",
    "MetricType",
    "AgentTelemetry",
    "Dashboard",
]
