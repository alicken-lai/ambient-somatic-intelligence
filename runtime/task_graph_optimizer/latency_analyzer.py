"""
Latency Analyzer — Analyze execution latency patterns in task graphs.

Provides per-node timing analysis, stage-level breakdown, percentile
calculations, and comparison between execution runs.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from runtime.task_graph.dag import TaskGraph, TaskNode, TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class NodeLatency:
    """Latency statistics for a single node."""
    node_id: str
    samples: int
    avg_ms: float
    min_ms: float
    max_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    variance: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "samples": self.samples,
            "avg_ms": round(self.avg_ms, 1),
            "min_ms": round(self.min_ms, 1),
            "max_ms": round(self.max_ms, 1),
            "p50_ms": round(self.p50_ms, 1),
            "p95_ms": round(self.p95_ms, 1),
            "p99_ms": round(self.p99_ms, 1),
            "variance": round(self.variance, 1),
        }


@dataclass
class StageLatency:
    """Latency for one parallel execution stage."""
    stage_index: int
    tasks: list[str]
    wall_clock_ms: float
    sum_task_ms: float
    parallelism_efficiency: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_index": self.stage_index,
            "tasks": self.tasks,
            "wall_clock_ms": round(self.wall_clock_ms, 1),
            "sum_task_ms": round(self.sum_task_ms, 1),
            "parallelism_efficiency": round(self.parallelism_efficiency, 3),
        }


@dataclass
class LatencyReport:
    """Complete latency analysis report."""
    per_node: list[NodeLatency]
    per_stage: list[StageLatency]
    total_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    slowest_nodes: list[str]
    latency_trends: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "per_node": [n.to_dict() for n in self.per_node],
            "per_stage": [s.to_dict() for s in self.per_stage],
            "total_ms": round(self.total_ms, 1),
            "p50_ms": round(self.p50_ms, 1),
            "p95_ms": round(self.p95_ms, 1),
            "p99_ms": round(self.p99_ms, 1),
            "slowest_nodes": self.slowest_nodes,
            "latency_trends": self.latency_trends,
        }


@dataclass
class LatencyComparison:
    """Comparison between two latency reports."""
    improved_nodes: list[dict[str, Any]]
    regressed_nodes: list[dict[str, Any]]
    total_change_ms: float
    total_change_pct: float
    verdict: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "improved_nodes": self.improved_nodes,
            "regressed_nodes": self.regressed_nodes,
            "total_change_ms": round(self.total_change_ms, 1),
            "total_change_pct": round(self.total_change_pct, 2),
            "verdict": self.verdict,
        }


class LatencyAnalyzer:
    """
    Analyze execution latency patterns in task graphs.

    Provides per-node timing statistics, stage-level breakdowns, percentile
    analysis, and run-to-run comparison.

    Usage:
        analyzer = LatencyAnalyzer()
        report = analyzer.analyze(graph)
        report = analyzer.analyze(graph, execution_history=history_data)
        comparison = analyzer.compare(report_a, report_b)
    """

    def analyze(
        self,
        graph: TaskGraph,
        execution_history: list[dict[str, Any]] | None = None,
    ) -> LatencyReport:
        """
        Perform latency analysis on a task graph.

        If execution_history is provided (list of past execution records for this graph),
        compute statistical summaries. Otherwise, use current graph node durations.
        """
        node_durations = self._collect_node_durations(graph, execution_history)
        per_node = self._compute_per_node_stats(node_durations)
        per_stage = self._compute_per_stage_stats(graph, node_durations)

        all_durations = []
        for durations in node_durations.values():
            all_durations.extend(durations)

        total_ms = sum(s.wall_clock_ms for s in per_stage) if per_stage else 0
        p50 = self._percentile(all_durations, 50)
        p95 = self._percentile(all_durations, 95)
        p99 = self._percentile(all_durations, 99)

        slowest = sorted(per_node, key=lambda n: n.avg_ms, reverse=True)
        slowest_nodes = [n.node_id for n in slowest[:5]]

        trends = self._compute_trends(execution_history) if execution_history else {}

        report = LatencyReport(
            per_node=per_node,
            per_stage=per_stage,
            total_ms=total_ms,
            p50_ms=p50,
            p95_ms=p95,
            p99_ms=p99,
            slowest_nodes=slowest_nodes,
            latency_trends=trends,
        )

        logger.info(
            "Latency analysis: total=%.1fms, p50=%.1fms, p95=%.1fms, nodes=%d",
            total_ms, p50, p95, len(per_node)
        )
        return report

    def compare(self, report_a: LatencyReport, report_b: LatencyReport) -> LatencyComparison:
        """
        Compare two latency reports, showing improvements and regressions.

        report_a is the baseline, report_b is the comparison target.
        """
        node_a_map = {n.node_id: n for n in report_a.per_node}
        node_b_map = {n.node_id: n for n in report_b.per_node}

        improved: list[dict[str, Any]] = []
        regressed: list[dict[str, Any]] = []

        all_node_ids = set(node_a_map.keys()) | set(node_b_map.keys())
        for node_id in all_node_ids:
            a = node_a_map.get(node_id)
            b = node_b_map.get(node_id)
            if not a or not b:
                continue

            change_ms = b.avg_ms - a.avg_ms
            change_pct = (change_ms / a.avg_ms * 100) if a.avg_ms > 0 else 0

            entry = {
                "node_id": node_id,
                "before_ms": round(a.avg_ms, 1),
                "after_ms": round(b.avg_ms, 1),
                "change_ms": round(change_ms, 1),
                "change_pct": round(change_pct, 1),
            }

            if change_ms < -10:
                improved.append(entry)
            elif change_ms > 10:
                regressed.append(entry)

        total_change = report_b.total_ms - report_a.total_ms
        total_change_pct = (
            (total_change / report_a.total_ms * 100) if report_a.total_ms > 0 else 0
        )

        if total_change_pct < -10:
            verdict = "significant_improvement"
        elif total_change_pct < -2:
            verdict = "minor_improvement"
        elif total_change_pct > 10:
            verdict = "significant_regression"
        elif total_change_pct > 2:
            verdict = "minor_regression"
        else:
            verdict = "no_significant_change"

        return LatencyComparison(
            improved_nodes=sorted(improved, key=lambda x: x["change_ms"]),
            regressed_nodes=sorted(regressed, key=lambda x: x["change_ms"], reverse=True),
            total_change_ms=total_change,
            total_change_pct=total_change_pct,
            verdict=verdict,
        )

    def _collect_node_durations(
        self,
        graph: TaskGraph,
        execution_history: list[dict[str, Any]] | None,
    ) -> dict[str, list[float]]:
        """Collect duration samples per node from graph state and history."""
        durations: dict[str, list[float]] = {nid: [] for nid in graph.nodes}

        for node_id, node in graph.nodes.items():
            if node.duration_ms is not None:
                durations[node_id].append(node.duration_ms)

        if execution_history:
            for record in execution_history:
                node_times = record.get("node_durations", {})
                for node_id, ms in node_times.items():
                    if node_id in durations:
                        durations[node_id].append(float(ms))

        return durations

    def _compute_per_node_stats(
        self, node_durations: dict[str, list[float]]
    ) -> list[NodeLatency]:
        """Compute statistical summaries per node."""
        stats: list[NodeLatency] = []

        for node_id, samples in node_durations.items():
            if not samples:
                stats.append(NodeLatency(
                    node_id=node_id,
                    samples=0,
                    avg_ms=0, min_ms=0, max_ms=0,
                    p50_ms=0, p95_ms=0, p99_ms=0,
                    variance=0,
                ))
                continue

            avg = sum(samples) / len(samples)
            variance = (
                sum((s - avg) ** 2 for s in samples) / len(samples)
                if len(samples) > 1 else 0
            )

            stats.append(NodeLatency(
                node_id=node_id,
                samples=len(samples),
                avg_ms=avg,
                min_ms=min(samples),
                max_ms=max(samples),
                p50_ms=self._percentile(samples, 50),
                p95_ms=self._percentile(samples, 95),
                p99_ms=self._percentile(samples, 99),
                variance=variance,
            ))

        return stats

    def _compute_per_stage_stats(
        self,
        graph: TaskGraph,
        node_durations: dict[str, list[float]],
    ) -> list[StageLatency]:
        """Compute latency for each parallel execution stage."""
        try:
            stages = graph.parallel_stages()
        except RuntimeError:
            return []

        stage_stats: list[StageLatency] = []

        for idx, stage_tasks in enumerate(stages):
            task_avgs: list[float] = []
            for task_id in stage_tasks:
                samples = node_durations.get(task_id, [])
                avg = sum(samples) / len(samples) if samples else 0
                task_avgs.append(avg)

            wall_clock = max(task_avgs) if task_avgs else 0
            sum_tasks = sum(task_avgs)
            efficiency = (sum_tasks / (wall_clock * len(task_avgs))) if wall_clock > 0 and task_avgs else 0

            stage_stats.append(StageLatency(
                stage_index=idx,
                tasks=stage_tasks,
                wall_clock_ms=wall_clock,
                sum_task_ms=sum_tasks,
                parallelism_efficiency=min(1.0, efficiency),
            ))

        return stage_stats

    def _compute_trends(
        self, execution_history: list[dict[str, Any]]
    ) -> dict[str, str]:
        """Compute latency trends from historical data."""
        if len(execution_history) < 3:
            return {"overall": "insufficient_data"}

        totals = []
        for record in execution_history:
            total = record.get("total_duration_ms", 0)
            if total > 0:
                totals.append(total)

        if len(totals) < 3:
            return {"overall": "insufficient_data"}

        recent = totals[-3:]
        older = totals[:-3] if len(totals) > 3 else totals[:1]

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older) if older else recent_avg

        if older_avg == 0:
            return {"overall": "stable"}

        change_pct = (recent_avg - older_avg) / older_avg * 100
        if change_pct < -10:
            trend = "improving"
        elif change_pct > 10:
            trend = "degrading"
        else:
            trend = "stable"

        return {
            "overall": trend,
            "recent_avg_ms": str(round(recent_avg, 1)),
            "older_avg_ms": str(round(older_avg, 1)),
            "change_pct": str(round(change_pct, 1)),
        }

    @staticmethod
    def _percentile(data: list[float], pct: int) -> float:
        """Compute a percentile value from a list of numbers."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        idx = (pct / 100) * (len(sorted_data) - 1)
        lower = int(math.floor(idx))
        upper = int(math.ceil(idx))
        if lower == upper:
            return sorted_data[lower]
        fraction = idx - lower
        return sorted_data[lower] * (1 - fraction) + sorted_data[upper] * fraction
