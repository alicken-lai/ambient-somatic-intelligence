"""
Dashboard — Unified status visualization for the Ambient OS.

Renders system state as structured text/ASCII for terminal or log output:
  - System health overview
  - Agent performance matrix
  - Memory layer utilization
  - Governance activity summary
  - Somatic signal timeline
  - Task DAG status
  - Token budget breakdown

Designed for both human consumption (pretty print) and machine parsing (JSON).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from observability.metrics_collector import MetricsCollector
from observability.telemetry import AgentTelemetry
from observability.tracer import ExecutionTracer


@dataclass
class DashboardConfig:
    """Dashboard display configuration."""
    width: int = 72
    show_agents: bool = True
    show_metrics: bool = True
    show_traces: bool = True
    show_somatic: bool = True
    show_dag: bool = True
    show_memory: bool = True
    max_recent_traces: int = 5
    max_recent_tasks: int = 10


class Dashboard:
    """
    Unified observability dashboard.

    Usage:
        metrics = MetricsCollector()
        telemetry = AgentTelemetry(metrics)
        tracer = ExecutionTracer()
        dashboard = Dashboard(metrics, telemetry, tracer)

        # Get full system snapshot
        state = dashboard.snapshot()

        # Render ASCII dashboard
        print(dashboard.render())

        # Get JSON-serializable report
        report = dashboard.report()
    """

    def __init__(
        self,
        metrics: MetricsCollector | None = None,
        telemetry: AgentTelemetry | None = None,
        tracer: ExecutionTracer | None = None,
        config: DashboardConfig | None = None,
        dag_visualizer: Any = None,
        signal_analytics: Any = None,
        memory_kernel: Any = None,
    ):
        self.metrics = metrics or MetricsCollector(persist=False)
        self.telemetry = telemetry or AgentTelemetry(self.metrics)
        self.tracer = tracer or ExecutionTracer(persist=False)
        self.config = config or DashboardConfig()
        self.dag_visualizer = dag_visualizer
        self.signal_analytics = signal_analytics
        self.memory_kernel = memory_kernel

    def snapshot(self) -> dict[str, Any]:
        """Get complete system state snapshot."""
        snap = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "health": self._health_summary(),
            "agents": self.telemetry.summary() if self.config.show_agents else {},
            "metrics": self.metrics.report_by_layer() if self.config.show_metrics else {},
            "traces": self.tracer.stats() if self.config.show_traces else {},
            "recent_tasks": self.telemetry.recent_tasks(self.config.max_recent_tasks),
        }
        if self.config.show_somatic and self.signal_analytics:
            try:
                snap["somatic_health"] = self.signal_analytics.health_report().to_dict()
            except Exception:
                snap["somatic_health"] = {"score": -1}
        if self.config.show_memory and self.memory_kernel:
            try:
                snap["memory_stats"] = self.memory_kernel.stats()
            except Exception:
                snap["memory_stats"] = {}
        return snap

    def report(self) -> dict[str, Any]:
        """Generate JSON-serializable report."""
        return self.snapshot()

    def render(self) -> str:
        """Render ASCII dashboard."""
        w = self.config.width
        lines: list[str] = []

        lines.append(self._header("AMBIENT OS — SYSTEM DASHBOARD", w))
        lines.append(f"  Time: {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("")

        lines.extend(self._render_health(w))
        lines.append("")

        if self.config.show_agents:
            lines.extend(self._render_agents(w))
            lines.append("")

        if self.config.show_metrics:
            lines.extend(self._render_metrics(w))
            lines.append("")

        if self.config.show_traces:
            lines.extend(self._render_traces(w))
            lines.append("")

        if self.config.show_somatic and self.signal_analytics:
            lines.extend(self._render_somatic(w))
            lines.append("")

        if self.config.show_memory and self.memory_kernel:
            lines.extend(self._render_memory(w))
            lines.append("")

        if self.config.show_dag and self.dag_visualizer:
            lines.extend(self._render_dag(w))
            lines.append("")

        lines.append("=" * w)
        return "\n".join(lines)

    def _health_summary(self) -> dict[str, Any]:
        """Calculate overall system health."""
        telemetry_summary = self.telemetry.summary()
        success_rate = telemetry_summary.get("overall_success_rate", 1.0)
        active_tasks = telemetry_summary.get("active_tasks", 0)
        tracer_stats = self.tracer.stats()
        error_count = tracer_stats.get("total_errors", 0)

        if success_rate >= 0.95 and error_count == 0:
            status = "HEALTHY"
        elif success_rate >= 0.8:
            status = "DEGRADED"
        else:
            status = "CRITICAL"

        return {
            "status": status,
            "success_rate": success_rate,
            "active_tasks": active_tasks,
            "total_errors": error_count,
        }

    def _header(self, title: str, width: int) -> str:
        """Render section header."""
        return f"{'=' * width}\n  {title}\n{'=' * width}"

    def _subheader(self, title: str, width: int) -> str:
        """Render subsection header."""
        return f"{'─' * width}\n  {title}\n{'─' * width}"

    def _render_health(self, w: int) -> list[str]:
        """Render health section."""
        health = self._health_summary()
        status_icons = {"HEALTHY": "[OK]", "DEGRADED": "[!!]", "CRITICAL": "[XX]"}
        icon = status_icons.get(health["status"], "[??]")

        lines = [self._subheader("SYSTEM HEALTH", w)]
        lines.append(f"  Status:       {icon} {health['status']}")
        lines.append(f"  Success Rate: {health['success_rate']:.1%}")
        lines.append(f"  Active Tasks: {health['active_tasks']}")
        lines.append(f"  Total Errors: {health['total_errors']}")
        return lines

    def _render_agents(self, w: int) -> list[str]:
        """Render agent performance section."""
        lines = [self._subheader("AGENT PERFORMANCE", w)]
        profiles = self.telemetry.all_profiles()

        if not profiles:
            lines.append("  No agents registered")
            return lines

        lines.append(f"  {'Agent':<20} {'Domain':<10} {'Done':<6} {'Fail':<6} {'Rate':<8} {'Tokens':<10}")
        lines.append(f"  {'─' * 20} {'─' * 10} {'─' * 6} {'─' * 6} {'─' * 8} {'─' * 10}")

        for p in profiles:
            lines.append(
                f"  {p['agent_id']:<20} "
                f"{p['domain']:<10} "
                f"{p['tasks_completed']:<6} "
                f"{p['tasks_failed']:<6} "
                f"{p['success_rate']:.1%}   "
                f"{p['total_tokens']:<10}"
            )

        return lines

    def _render_metrics(self, w: int) -> list[str]:
        """Render metrics section."""
        lines = [self._subheader("KEY METRICS", w)]
        report = self.metrics.report()

        counters = report.get("counters", {})
        if counters:
            top_counters = sorted(counters.items(), key=lambda x: x[1], reverse=True)[:8]
            for name, val in top_counters:
                bar_len = min(int(val / max(c[1] for c in top_counters) * 30), 30) if top_counters else 0
                bar = "█" * bar_len
                lines.append(f"  {name:<35} {val:>8.0f}  {bar}")
        else:
            lines.append("  No metrics recorded yet")

        histograms = report.get("histograms", {})
        if histograms:
            lines.append("")
            lines.append(f"  {'Histogram':<30} {'avg':<8} {'p50':<8} {'p95':<8} {'p99':<8}")
            lines.append(f"  {'─' * 30} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8}")
            for name, stats in list(histograms.items())[:5]:
                lines.append(
                    f"  {name:<30} "
                    f"{stats['avg']:<8.1f} "
                    f"{stats['p50']:<8.1f} "
                    f"{stats['p95']:<8.1f} "
                    f"{stats['p99']:<8.1f}"
                )

        return lines

    def _render_traces(self, w: int) -> list[str]:
        """Render recent traces section."""
        lines = [self._subheader("RECENT TRACES", w)]
        stats = self.tracer.stats()

        lines.append(f"  Total Traces: {stats['total_traces']}  |  Spans: {stats['total_spans']}  |  Errors: {stats['total_errors']}")
        lines.append(f"  Avg Duration: {stats['avg_duration_ms']:.0f}ms")
        lines.append("")

        recent = self.tracer.recent_traces(self.config.max_recent_traces)
        if recent:
            lines.append(f"  {'Trace':<14} {'Spans':<7} {'Duration':<12} {'Errors':<7}")
            lines.append(f"  {'─' * 14} {'─' * 7} {'─' * 12} {'─' * 7}")
            for t in recent:
                trace_id = t["trace_id"][:12]
                dur = f"{t['duration_ms']:.0f}ms" if t["duration_ms"] else "active"
                lines.append(f"  {trace_id:<14} {t['span_count']:<7} {dur:<12} {t['error_count']:<7}")
        else:
            lines.append("  No traces recorded yet")

        return lines

    def _render_somatic(self, w: int) -> list[str]:
        """Render somatic health section."""
        lines = [self._subheader("SOMATIC HEALTH", w)]
        try:
            report = self.signal_analytics.health_report()
            lines.append(f"  Health Score: {report.score:.2f}  |  Grade: {report.grade}")
            for factor_name, factor_val in report.factors.items():
                bar_len = int(factor_val * 20)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                lines.append(f"  {factor_name:<12} {bar} {factor_val:.2f}")
            if report.recommendations:
                lines.append("")
                for rec in report.recommendations[:3]:
                    lines.append(f"    - {rec}")
        except Exception:
            lines.append("  Somatic analytics unavailable")
        return lines

    def _render_memory(self, w: int) -> list[str]:
        """Render memory kernel stats section."""
        lines = [self._subheader("MEMORY KERNEL", w)]
        try:
            stats = self.memory_kernel.stats()
            lines.append(f"  Total Records: {stats.get('total_records', 0)}")
            layers = stats.get("layers", {})
            if layers:
                for layer_name, count in layers.items():
                    lines.append(f"    {layer_name:<20} {count} records")
        except Exception:
            lines.append("  Memory kernel stats unavailable")
        return lines

    def _render_dag(self, w: int) -> list[str]:
        """Render DAG visualization section."""
        lines = [self._subheader("DAG EXECUTION", w)]
        lines.append("  DAG Visualizer: active")
        lines.append("  Use dashboard.dag_visualizer.to_ascii(graph) for live rendering")
        return lines

    def render_compact(self) -> str:
        """Render one-line status."""
        health = self._health_summary()
        summary = self.telemetry.summary()
        return (
            f"[{health['status']}] "
            f"agents={summary['agents_registered']} "
            f"active={summary['active_tasks']} "
            f"done={summary['total_completed']} "
            f"fail={summary['total_failed']} "
            f"tokens={summary['total_tokens_consumed']}"
        )
