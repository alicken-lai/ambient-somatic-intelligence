"""
Introspection Dashboard — System self-awareness visualization.

Renders a comprehensive view of the system's internal cognitive state:
  - Cognition trace summary (decision patterns)
  - Memory flow summary (access patterns)
  - Context assembly efficiency (budget usage)
  - Governance load (gate check throughput)
  - Recursive telemetry (observability health)
  - System stress level

Unlike the standard Dashboard which shows execution metrics,
the Introspection Dashboard shows meta-cognitive patterns —
how the system thinks about thinking.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from observability.recursive_runtime.cognition_tracer import CognitionTracer
from observability.recursive_runtime.memory_flow_tracer import MemoryFlowTracer
from observability.recursive_runtime.context_assembly_tracer import ContextAssemblyTracer
from observability.recursive_runtime.governance_analytics import GovernanceLoadAnalytics
from observability.recursive_runtime.recursive_telemetry import RecursiveTelemetry

logger = logging.getLogger(__name__)


class IntrospectionDashboard:
    """
    System introspection dashboard for meta-cognitive observability.

    Renders a comprehensive view of the system's internal decision-making,
    memory access patterns, context assembly efficiency, governance health,
    and observability stack status.

    Usage:
        cognition = CognitionTracer()
        memory_flow = MemoryFlowTracer()
        context = ContextAssemblyTracer()
        governance = GovernanceLoadAnalytics()
        recursive = RecursiveTelemetry()

        dashboard = IntrospectionDashboard(
            cognition_tracer=cognition,
            memory_flow_tracer=memory_flow,
            context_tracer=context,
            governance_analytics=governance,
            recursive_telemetry=recursive,
        )

        print(dashboard.render())
        data = dashboard.to_dict()
    """

    def __init__(
        self,
        cognition_tracer: CognitionTracer | None = None,
        memory_flow_tracer: MemoryFlowTracer | None = None,
        context_tracer: ContextAssemblyTracer | None = None,
        governance_analytics: GovernanceLoadAnalytics | None = None,
        recursive_telemetry: RecursiveTelemetry | None = None,
        width: int = 76,
    ):
        self._cognition = cognition_tracer or CognitionTracer(persist=False)
        self._memory_flow = memory_flow_tracer or MemoryFlowTracer(persist=False)
        self._context = context_tracer or ContextAssemblyTracer(persist=False)
        self._governance = governance_analytics or GovernanceLoadAnalytics()
        self._recursive = recursive_telemetry or RecursiveTelemetry()
        self._width = width

    def render(self) -> str:
        """
        Render comprehensive ASCII introspection dashboard.

        Shows cognition traces, memory flow, context assembly,
        governance load, recursive telemetry, and system stress.
        """
        w = self._width
        lines: list[str] = []

        lines.append(self._header("AMBIENT OS — INTROSPECTION DASHBOARD", w))
        lines.append(f"  Time: {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("")

        lines.extend(self._render_cognition(w))
        lines.append("")
        lines.extend(self._render_memory_flow(w))
        lines.append("")
        lines.extend(self._render_context_assembly(w))
        lines.append("")
        lines.extend(self._render_governance(w))
        lines.append("")
        lines.extend(self._render_recursive_telemetry(w))
        lines.append("")
        lines.extend(self._render_stress_level(w))
        lines.append("")

        lines.append("=" * w)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Get structured dashboard data as a JSON-serializable dict."""
        cognition_stats = self._cognition.stats()
        memory_summary = self._memory_flow.get_flow_summary()
        context_report = self._context.get_assembly_report()
        governance_load = self._governance.get_governance_load()
        recursive_report = self._recursive.collect()

        return {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "cognition": cognition_stats,
            "memory_flow": memory_summary.to_dict(),
            "context_assembly": context_report.to_dict(),
            "governance": governance_load.to_dict(),
            "recursive_telemetry": recursive_report.to_dict(),
            "stress_level": self._compute_stress_level(),
        }

    def to_markdown(self) -> str:
        """Generate markdown-formatted introspection report."""
        data = self.to_dict()
        lines: list[str] = []

        lines.append("# Ambient OS Introspection Report")
        lines.append(f"\n**Generated:** {data['timestamp']}")
        lines.append(f"\n**Stress Level:** {data['stress_level']['level']} "
                     f"({data['stress_level']['score']:.2f})")

        lines.append("\n## Cognition Traces")
        cog = data["cognition"]
        lines.append(f"- Total traces: {cog['total_traces']}")
        lines.append(f"- Reasoning chains: {cog['total_chains']}")
        lines.append(f"- Avg decision time: {cog['avg_duration_ms']:.1f}ms")
        if cog.get("by_type"):
            lines.append("- By type:")
            for dtype, count in cog["by_type"].items():
                lines.append(f"  - {dtype}: {count}")

        lines.append("\n## Memory Flow")
        mem = data["memory_flow"]
        lines.append(f"- Total recalls: {mem['total_recalls']}")
        lines.append(f"- Total stores: {mem['total_stores']}")
        lines.append(f"- Avg latency: {mem['avg_latency_ms']:.1f}ms")
        lines.append(f"- Hit rate: {mem['hit_rate']:.1%}")
        lines.append(f"- Compression ratio: {mem['compression_ratio']:.2f}")

        lines.append("\n## Context Assembly")
        ctx = data["context_assembly"]
        lines.append(f"- Total assemblies: {ctx['total_assemblies']}")
        lines.append(f"- Avg tokens: {ctx['avg_tokens']:.0f}")
        lines.append(f"- Budget utilization: {ctx['budget_utilization']:.1%}")
        lines.append(f"- Retrieval efficiency: {ctx['retrieval_efficiency']:.1%}")
        lines.append(f"- Waste ratio: {ctx['waste_ratio']:.1%}")

        lines.append("\n## Governance")
        gov = data["governance"]
        lines.append(f"- Checks/min: {gov['checks_per_minute']:.1f}")
        lines.append(f"- Avg latency: {gov['avg_latency_ms']:.1f}ms")
        lines.append(f"- Approval rate: {gov['approval_rate']:.1%}")
        lines.append(f"- Bottleneck score: {gov['bottleneck_score']:.2f}")

        lines.append("\n## Observability Health")
        rec = data["recursive_telemetry"]
        lines.append(f"- Overhead: {rec['overhead_pct']:.2f}%")
        lines.append(f"- Pipeline latency: {rec['pipeline_latency_ms']:.1f}ms")
        if rec.get("recommendations"):
            lines.append("- Recommendations:")
            for r in rec["recommendations"]:
                lines.append(f"  - {r}")

        return "\n".join(lines)

    def _compute_stress_level(self) -> dict[str, Any]:
        """Compute overall system stress from all subsystems."""
        scores: list[float] = []

        governance_load = self._governance.get_governance_load()
        scores.append(governance_load.bottleneck_score)

        memory_summary = self._memory_flow.get_flow_summary()
        if memory_summary.avg_latency_ms > 0:
            memory_stress = min(1.0, memory_summary.avg_latency_ms / 200.0)
            scores.append(memory_stress)

        context_report = self._context.get_assembly_report()
        if context_report.waste_ratio > 0:
            scores.append(min(1.0, context_report.waste_ratio * 2))

        overhead = self._recursive.get_observability_overhead()
        scores.append(min(1.0, overhead / 10.0))

        overall = sum(scores) / len(scores) if scores else 0.0

        if overall < 0.3:
            level = "LOW"
        elif overall < 0.6:
            level = "MODERATE"
        elif overall < 0.8:
            level = "HIGH"
        else:
            level = "CRITICAL"

        return {
            "score": round(overall, 4),
            "level": level,
            "components": {
                "governance": round(governance_load.bottleneck_score, 4),
                "overhead": round(overhead / 10.0, 4),
            },
        }

    def _header(self, title: str, width: int) -> str:
        """Render section header."""
        return f"{'=' * width}\n  {title}\n{'=' * width}"

    def _subheader(self, title: str, width: int) -> str:
        """Render subsection header."""
        return f"{'─' * width}\n  {title}\n{'─' * width}"

    def _render_cognition(self, w: int) -> list[str]:
        """Render cognition trace summary."""
        lines = [self._subheader("COGNITION TRACES", w)]
        stats = self._cognition.stats()

        lines.append(f"  Total Decisions: {stats['total_traces']}")
        lines.append(f"  Reasoning Chains: {stats['total_chains']}")
        lines.append(f"  Avg Decision Time: {stats['avg_duration_ms']:.1f}ms")

        by_type = stats.get("by_type", {})
        if by_type:
            lines.append("")
            lines.append(f"  {'Type':<15} {'Count':<8} {'Distribution'}")
            lines.append(f"  {'─' * 15} {'─' * 8} {'─' * 30}")
            total = sum(by_type.values()) or 1
            for dtype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
                pct = count / total
                bar = "█" * int(pct * 25)
                lines.append(f"  {dtype:<15} {count:<8} {bar} {pct:.0%}")
        else:
            lines.append("  No decisions recorded yet")

        return lines

    def _render_memory_flow(self, w: int) -> list[str]:
        """Render memory flow summary."""
        lines = [self._subheader("MEMORY FLOW", w)]
        summary = self._memory_flow.get_flow_summary()

        lines.append(f"  Recalls: {summary.total_recalls}  |  Stores: {summary.total_stores}")
        lines.append(f"  Avg Latency: {summary.avg_latency_ms:.1f}ms  |  Hit Rate: {summary.hit_rate:.1%}")
        lines.append(f"  Compression Ratio: {summary.compression_ratio:.2f}")

        if summary.hot_queries:
            lines.append("")
            lines.append("  Hot Queries:")
            for hq in summary.hot_queries[:5]:
                lines.append(f"    [{hq['count']:>3}x] {hq['query'][:50]}")

        return lines

    def _render_context_assembly(self, w: int) -> list[str]:
        """Render context assembly efficiency."""
        lines = [self._subheader("CONTEXT ASSEMBLY", w)]
        report = self._context.get_assembly_report()

        lines.append(f"  Assemblies: {report.total_assemblies}")
        lines.append(f"  Avg Tokens: {report.avg_tokens:.0f}")
        lines.append(f"  Budget Utilization: {report.budget_utilization:.1%}")
        lines.append(f"  Retrieval Efficiency: {report.retrieval_efficiency:.1%}")
        lines.append(f"  Waste Ratio: {report.waste_ratio:.1%}")

        if report.top_sources:
            lines.append("")
            lines.append("  Top Sources:")
            for src in report.top_sources[:5]:
                lines.append(f"    {src['source']:<20} ({src['count']}x)")

        return lines

    def _render_governance(self, w: int) -> list[str]:
        """Render governance load."""
        lines = [self._subheader("GOVERNANCE LOAD", w)]
        load = self._governance.get_governance_load()

        lines.append(f"  Checks/min: {load.checks_per_minute:.1f}")
        lines.append(f"  Avg Latency: {load.avg_latency_ms:.1f}ms")
        lines.append(f"  Approval: {load.approval_rate:.1%}  |  Denial: {load.denial_rate:.1%}  |  Review: {load.review_rate:.1%}")
        lines.append(f"  Bottleneck Score: {load.bottleneck_score:.2f}  |  Effectiveness: {load.effectiveness_score:.2f}")

        return lines

    def _render_recursive_telemetry(self, w: int) -> list[str]:
        """Render recursive telemetry health."""
        lines = [self._subheader("OBSERVABILITY HEALTH", w)]
        report = self._recursive.collect()

        healthy_icon = "[OK]" if self._recursive.is_healthy() else "[!!]"
        lines.append(f"  Status: {healthy_icon}")
        lines.append(f"  Overhead: {report.overhead_pct:.2f}%")
        lines.append(f"  Pipeline Latency: {report.pipeline_latency_ms:.1f}ms")
        lines.append(f"  Tracer: {report.tracer_health.traces_per_minute:.1f} traces/min")
        lines.append(f"  Metrics: {report.metrics_health.metric_count} metrics tracked")

        if report.recommendations:
            lines.append("")
            lines.append("  Recommendations:")
            for rec in report.recommendations:
                lines.append(f"    ⚠ {rec}")

        return lines

    def _render_stress_level(self, w: int) -> list[str]:
        """Render system stress level."""
        lines = [self._subheader("SYSTEM STRESS", w)]
        stress = self._compute_stress_level()

        icons = {"LOW": "[OK]", "MODERATE": "[~~]", "HIGH": "[!!]", "CRITICAL": "[XX]"}
        icon = icons.get(stress["level"], "[??]")

        bar_len = int(stress["score"] * 40)
        bar = "█" * bar_len + "░" * (40 - bar_len)

        lines.append(f"  Level: {icon} {stress['level']} ({stress['score']:.2f})")
        lines.append(f"  [{bar}]")

        return lines
