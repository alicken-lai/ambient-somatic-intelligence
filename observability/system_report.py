"""
System Report — Unified health report aggregating ALL Ambient OS subsystems.

The "one report to rule them all" — pulls health data from every layer:
  - Memory: kernel stats, recall volume, TTL expirations
  - Somatic: health score, signal analytics, attention level
  - Governance: audit stats, block/review rates, policy hits
  - Agents: telemetry profiles, success rates, token consumption
  - Tasks: execution history, DAG progress, failure rates
  - Context: injection stats, token budget usage
  - Observability: trace stats, decision log stats

Output formats:
  - generate() → structured dict
  - render_ascii() → terminal-friendly text
  - render_json() → JSON-serializable dict
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import AmbientKernel


@dataclass
class ReportSection:
    """A single section of the system report."""
    name: str
    status: str
    data: dict[str, Any]
    recommendations: list[str] = field(default_factory=list)


class SystemReport:
    """
    Aggregates health from ALL subsystems into a unified report.

    Usage:
        from kernel import AmbientKernel
        kernel = AmbientKernel.boot()
        report = SystemReport(kernel)

        full = report.generate()
        print(report.render_ascii())
        json_data = report.render_json()
    """

    def __init__(self, kernel: "AmbientKernel"):
        self.kernel = kernel

    def generate(self) -> dict[str, Any]:
        """Generate a comprehensive system health report."""
        sections = {
            "executive_summary": self._executive_summary(),
            "memory_health": self._memory_health(),
            "somatic_state": self._somatic_state(),
            "governance_activity": self._governance_activity(),
            "agent_performance": self._agent_performance(),
            "task_execution": self._task_execution(),
            "context_budget": self._context_budget(),
            "observability_stats": self._observability_stats(),
            "recommendations": self._recommendations(),
        }

        return {
            "report_type": "system_health",
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "version": getattr(self.kernel, '__version__', '0.2.0-alpha'),
            "sections": sections,
        }

    def render_json(self) -> dict[str, Any]:
        """Alias for generate() — JSON-serializable output."""
        return self.generate()

    def render_ascii(self) -> str:
        """Render a terminal-friendly text report."""
        w = 72
        data = self.generate()
        lines: list[str] = []

        lines.append("=" * w)
        lines.append("  AMBIENT OS — UNIFIED SYSTEM HEALTH REPORT")
        lines.append("=" * w)
        lines.append(f"  Generated: {data['timestamp']}")
        lines.append("")

        exec_sum = data["sections"]["executive_summary"]
        lines.append(self._section_header("EXECUTIVE SUMMARY", w))
        lines.append(f"  Overall Status:  {exec_sum.get('overall_status', 'UNKNOWN')}")
        lines.append(f"  Health Score:    {exec_sum.get('health_score', 'N/A')}")
        lines.append(f"  Active Agents:   {exec_sum.get('agents_registered', 0)}")
        lines.append(f"  Active Tasks:    {exec_sum.get('active_tasks', 0)}")
        lines.append(f"  Total Traces:    {exec_sum.get('total_traces', 0)}")
        lines.append("")

        mem = data["sections"]["memory_health"]
        lines.append(self._section_header("MEMORY HEALTH", w))
        for key, val in mem.items():
            lines.append(f"  {key:<30} {val}")
        lines.append("")

        somatic = data["sections"]["somatic_state"]
        lines.append(self._section_header("SOMATIC STATE", w))
        for key, val in somatic.items():
            if not isinstance(val, (dict, list)):
                lines.append(f"  {key:<30} {val}")
        lines.append("")

        gov = data["sections"]["governance_activity"]
        lines.append(self._section_header("GOVERNANCE ACTIVITY", w))
        for key, val in gov.items():
            if not isinstance(val, (dict, list)):
                lines.append(f"  {key:<30} {val}")
        lines.append("")

        agents = data["sections"]["agent_performance"]
        lines.append(self._section_header("AGENT PERFORMANCE", w))
        lines.append(f"  Registered:       {agents.get('agents_registered', 0)}")
        lines.append(f"  Total Completed:  {agents.get('total_completed', 0)}")
        lines.append(f"  Success Rate:     {agents.get('overall_success_rate', 'N/A')}")
        lines.append("")

        tasks = data["sections"]["task_execution"]
        lines.append(self._section_header("TASK EXECUTION", w))
        for key, val in tasks.items():
            if not isinstance(val, (dict, list)):
                lines.append(f"  {key:<30} {val}")
        lines.append("")

        ctx = data["sections"]["context_budget"]
        lines.append(self._section_header("CONTEXT BUDGET", w))
        for key, val in ctx.items():
            if not isinstance(val, (dict, list)):
                lines.append(f"  {key:<30} {val}")
        lines.append("")

        recs = data["sections"]["recommendations"]
        lines.append(self._section_header("RECOMMENDATIONS", w))
        if recs:
            for i, rec in enumerate(recs, 1):
                lines.append(f"  {i}. {rec}")
        else:
            lines.append("  System is operating within normal parameters")
        lines.append("")

        lines.append("=" * w)
        return "\n".join(lines)

    @staticmethod
    def _section_header(title: str, width: int) -> str:
        return f"{'─' * width}\n  {title}\n{'─' * width}"

    def _executive_summary(self) -> dict[str, Any]:
        """High-level system overview."""
        k = self.kernel
        result: dict[str, Any] = {}

        try:
            telemetry_summary = k.observability.telemetry.summary()
            result["agents_registered"] = telemetry_summary.get("agents_registered", 0)
            result["active_tasks"] = telemetry_summary.get("active_tasks", 0)
            result["overall_success_rate"] = telemetry_summary.get("overall_success_rate", 1.0)
        except Exception:
            result["agents_registered"] = 0
            result["active_tasks"] = 0
            result["overall_success_rate"] = 1.0

        try:
            tracer_stats = k.observability.tracer.stats()
            result["total_traces"] = tracer_stats.get("total_traces", 0)
            result["total_errors"] = tracer_stats.get("total_errors", 0)
        except Exception:
            result["total_traces"] = 0
            result["total_errors"] = 0

        try:
            health_score = k.somatic.analytics.health_score()
            result["health_score"] = round(health_score, 4)
        except Exception:
            result["health_score"] = 1.0

        score = result["health_score"]
        success_rate = result["overall_success_rate"]
        errors = result["total_errors"]

        if score >= 0.8 and success_rate >= 0.95 and errors == 0:
            result["overall_status"] = "HEALTHY"
        elif score >= 0.5 and success_rate >= 0.7:
            result["overall_status"] = "DEGRADED"
        else:
            result["overall_status"] = "CRITICAL"

        return result

    def _memory_health(self) -> dict[str, Any]:
        """Memory subsystem health."""
        try:
            stats = self.kernel.memory.stats()
            return {
                "total_records": stats.get("total_records", 0),
                "layers": stats.get("layers", {}),
                "ttl_expirations": stats.get("ttl_expirations", 0),
                "dedup_count": stats.get("dedup_count", 0),
            }
        except Exception:
            return {"status": "unavailable"}

    def _somatic_state(self) -> dict[str, Any]:
        """Somatic signal bus state."""
        result: dict[str, Any] = {}
        try:
            bus_state = self.kernel.somatic.bus.current_state()
            result["bus_state"] = bus_state
        except Exception:
            result["bus_state"] = "unavailable"

        try:
            attention = self.kernel.somatic.attention.current_state()
            result["attention_level"] = attention.level.label
            result["governance_sensitivity"] = attention.governance_sensitivity
        except Exception:
            pass

        try:
            report = self.kernel.somatic.analytics.health_report()
            result["health_score"] = round(report.score, 4)
            result["health_grade"] = report.grade
        except Exception:
            pass

        return result

    def _governance_activity(self) -> dict[str, Any]:
        """Governance subsystem activity."""
        try:
            stats = self.kernel.governance.audit_log.stats(hours=1)
            return {
                "decisions_1h": stats.get("total", 0),
                "block_rate": stats.get("block_rate", 0),
                "review_rate": stats.get("review_rate", 0),
                "by_risk": stats.get("by_risk", {}),
                "top_policies": stats.get("top_policies", []),
            }
        except Exception:
            return {"status": "unavailable"}

    def _agent_performance(self) -> dict[str, Any]:
        """Agent runtime performance."""
        try:
            summary = self.kernel.observability.telemetry.summary()
            return {
                "agents_registered": summary.get("agents_registered", 0),
                "total_completed": summary.get("total_completed", 0),
                "total_failed": summary.get("total_failed", 0),
                "overall_success_rate": summary.get("overall_success_rate", 1.0),
                "total_tokens_consumed": summary.get("total_tokens_consumed", 0),
                "profiles": summary.get("agent_profiles", []),
            }
        except Exception:
            return {"status": "unavailable"}

    def _task_execution(self) -> dict[str, Any]:
        """Task graph execution stats."""
        result: dict[str, Any] = {}
        try:
            tracer_stats = self.kernel.observability.tracer.stats()
            result["total_traces"] = tracer_stats.get("total_traces", 0)
            result["total_spans"] = tracer_stats.get("total_spans", 0)
            result["avg_duration_ms"] = tracer_stats.get("avg_duration_ms", 0)
        except Exception:
            result["tracer"] = "unavailable"

        try:
            active = self.kernel.observability.telemetry.active_tasks()
            result["active_tasks"] = len(active)
        except Exception:
            result["active_tasks"] = 0

        return result

    def _context_budget(self) -> dict[str, Any]:
        """Context engine budget usage."""
        result: dict[str, Any] = {}
        try:
            bm = self.kernel.context.budget_manager
            if hasattr(bm, 'total_budget'):
                result["total_budget"] = bm.total_budget
        except Exception:
            pass

        try:
            inj_stats = self.kernel.context.injection_logger.stats(hours=1)
            result["injections_1h"] = inj_stats.get("total_injections", 0)
            result["tokens_injected_1h"] = inj_stats.get("total_tokens", 0)
            result["avg_tokens_per_injection"] = inj_stats.get("avg_tokens_per_injection", 0)
        except Exception:
            pass

        return result

    def _observability_stats(self) -> dict[str, Any]:
        """Observability layer self-stats."""
        result: dict[str, Any] = {}
        try:
            result["tracer"] = self.kernel.observability.tracer.stats()
        except Exception:
            result["tracer"] = "unavailable"

        try:
            result["metrics"] = {
                "counters": len(self.kernel.observability.metrics._counters),
                "gauges": len(self.kernel.observability.metrics._gauges),
                "histograms": len(self.kernel.observability.metrics._histograms),
            }
        except Exception:
            result["metrics"] = "unavailable"

        try:
            decision_log = self.kernel.observability.decision_log
            result["decision_log"] = decision_log.stats()
        except Exception:
            result["decision_log"] = "unavailable"

        return result

    def _recommendations(self) -> list[str]:
        """Generate actionable recommendations based on current state."""
        recs: list[str] = []

        try:
            report = self.kernel.somatic.analytics.health_report()
            recs.extend(report.recommendations)
        except Exception:
            pass

        try:
            summary = self.kernel.observability.telemetry.summary()
            sr = summary.get("overall_success_rate", 1.0)
            if sr < 0.9:
                recs.append(
                    f"Agent success rate is {sr:.0%} — investigate failing tasks"
                )
        except Exception:
            pass

        try:
            tracer_stats = self.kernel.observability.tracer.stats()
            if tracer_stats.get("total_errors", 0) > 5:
                recs.append(
                    f"{tracer_stats['total_errors']} trace errors — review execution logs"
                )
        except Exception:
            pass

        if not recs:
            recs.append("All subsystems operating within normal parameters")

        return recs
