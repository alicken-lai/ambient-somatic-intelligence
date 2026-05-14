"""
Task Graph Optimizer — Unified optimizer combining all analyzers to produce
comprehensive optimization proposals for task execution graphs.

Orchestrates bottleneck detection, latency analysis, dependency compression,
and redundancy detection into a single optimization pipeline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from runtime.task_graph.dag import TaskGraph, TaskNode
from runtime.task_graph_optimizer.bottleneck_detector import (
    BottleneckDetector,
    BottleneckReport,
)
from runtime.task_graph_optimizer.latency_analyzer import (
    LatencyAnalyzer,
    LatencyReport,
)
from runtime.task_graph_optimizer.dependency_compressor import (
    DependencyCompressor,
    CompressionProposal,
)
from runtime.task_graph_optimizer.redundancy_detector import (
    RedundancyDetector,
    RedundancyReport,
)

logger = logging.getLogger(__name__)


@dataclass
class GraphMetrics:
    """Structural metrics for a task graph."""
    node_count: int
    edge_count: int
    stage_count: int
    critical_path_length: int
    max_parallelism: int
    estimated_latency_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "stage_count": self.stage_count,
            "critical_path_length": self.critical_path_length,
            "max_parallelism": self.max_parallelism,
            "estimated_latency_ms": round(self.estimated_latency_ms, 1),
        }


@dataclass
class Recommendation:
    """A specific optimization recommendation."""
    priority: int  # 1 = highest
    category: str
    description: str
    expected_benefit: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "priority": self.priority,
            "category": self.category,
            "description": self.description,
            "expected_benefit": self.expected_benefit,
        }


@dataclass
class OptimizationResult:
    """Complete result of a graph optimization analysis."""
    bottleneck_report: BottleneckReport
    latency_report: LatencyReport
    compression_proposal: CompressionProposal
    redundancy_report: RedundancyReport
    overall_score: float
    recommendations: list[Recommendation]
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "bottleneck_report": self.bottleneck_report.to_dict(),
            "latency_report": self.latency_report.to_dict(),
            "compression_proposal": self.compression_proposal.to_dict(),
            "redundancy_report": self.redundancy_report.to_dict(),
            "overall_score": round(self.overall_score, 3),
            "recommendations": [r.to_dict() for r in self.recommendations],
            "timestamp": self.timestamp,
        }


@dataclass
class BenchmarkResult:
    """Comparison between original and optimized graphs."""
    original_metrics: GraphMetrics
    optimized_metrics: GraphMetrics
    improvements: dict[str, Any]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_metrics": self.original_metrics.to_dict(),
            "optimized_metrics": self.optimized_metrics.to_dict(),
            "improvements": self.improvements,
            "warnings": self.warnings,
        }


class TaskGraphOptimizer:
    """
    Unified task graph optimizer that combines all analyzers.

    Orchestrates bottleneck detection, latency analysis, dependency compression,
    and redundancy detection to produce comprehensive optimization results.

    All proposals are explainable, benchmarked, and reversible — the original
    graph is never modified.

    Usage:
        optimizer = TaskGraphOptimizer()
        result = optimizer.optimize(graph)
        candidate = optimizer.generate_optimized_candidate(graph, result)
        benchmark = optimizer.benchmark(graph, candidate)
        print(optimizer.to_report(result, benchmark))
    """

    def __init__(
        self,
        bottleneck_detector: BottleneckDetector | None = None,
        latency_analyzer: LatencyAnalyzer | None = None,
        dependency_compressor: DependencyCompressor | None = None,
        redundancy_detector: RedundancyDetector | None = None,
    ):
        self._bottleneck = bottleneck_detector or BottleneckDetector()
        self._latency = latency_analyzer or LatencyAnalyzer()
        self._compressor = dependency_compressor or DependencyCompressor()
        self._redundancy = redundancy_detector or RedundancyDetector()

    def optimize(
        self,
        graph: TaskGraph,
        execution_history: list[dict[str, Any]] | None = None,
    ) -> OptimizationResult:
        """
        Run all analyzers on a graph and generate an optimization proposal.

        Returns a comprehensive OptimizationResult with reports from each
        analyzer and ranked recommendations.
        """
        execution_results = self._build_execution_results(graph, execution_history)

        bottleneck_report = self._bottleneck.detect(graph, execution_results)
        latency_report = self._latency.analyze(graph, execution_history)
        compression_proposal = self._compressor.analyze(graph)
        redundancy_report = self._redundancy.detect(graph)

        overall_score = self._compute_overall_score(
            bottleneck_report, latency_report, compression_proposal, redundancy_report
        )

        recommendations = self._generate_recommendations(
            bottleneck_report, latency_report, compression_proposal, redundancy_report
        )

        result = OptimizationResult(
            bottleneck_report=bottleneck_report,
            latency_report=latency_report,
            compression_proposal=compression_proposal,
            redundancy_report=redundancy_report,
            overall_score=overall_score,
            recommendations=recommendations,
        )

        logger.info(
            "Optimization complete: score=%.3f, %d recommendations",
            overall_score, len(recommendations)
        )
        return result

    def generate_optimized_candidate(
        self, graph: TaskGraph, optimization_result: OptimizationResult
    ) -> TaskGraph:
        """
        Create an optimized graph candidate based on optimization results.

        The original graph is NOT modified. Returns a new graph with
        compression proposals applied.
        """
        proposal = optimization_result.compression_proposal
        optimized, _ = self._compressor.simulate_compression(graph, proposal)

        redundancy = optimization_result.redundancy_report
        for noop in redundancy.noop_nodes:
            if noop.node_id in optimized.nodes:
                dependents = optimized.get_dependents(noop.node_id)
                deps = optimized.get_dependencies(noop.node_id)

                for dep in deps:
                    for dependent in dependents:
                        try:
                            optimized.add_edge(dep, dependent)
                        except ValueError:
                            pass

                optimized.edges = [
                    e for e in optimized.edges
                    if e.source != noop.node_id and e.target != noop.node_id
                ]
                del optimized.nodes[noop.node_id]

        return optimized

    def benchmark(
        self, original: TaskGraph, optimized: TaskGraph
    ) -> BenchmarkResult:
        """
        Compare original and optimized graphs across multiple dimensions.

        Returns metrics for both graphs and computed improvements.
        """
        original_metrics = self._compute_metrics(original)
        optimized_metrics = self._compute_metrics(optimized)

        improvements = self._compute_improvements(original_metrics, optimized_metrics)
        warnings = self._generate_warnings(original, optimized, improvements)

        result = BenchmarkResult(
            original_metrics=original_metrics,
            optimized_metrics=optimized_metrics,
            improvements=improvements,
            warnings=warnings,
        )

        logger.info(
            "Benchmark: nodes %d→%d, edges %d→%d, stages %d→%d",
            original_metrics.node_count, optimized_metrics.node_count,
            original_metrics.edge_count, optimized_metrics.edge_count,
            original_metrics.stage_count, optimized_metrics.stage_count,
        )
        return result

    def to_report(
        self,
        result: OptimizationResult,
        benchmark: BenchmarkResult | None = None,
    ) -> str:
        """Generate a human-readable optimization report."""
        lines: list[str] = []
        lines.append("=" * 60)
        lines.append("TASK GRAPH OPTIMIZATION REPORT")
        lines.append("=" * 60)
        lines.append(f"Timestamp: {result.timestamp}")
        lines.append(f"Overall Optimization Score: {result.overall_score:.3f}")
        lines.append("")

        lines.append("--- BOTTLENECK ANALYSIS ---")
        lines.append(f"Bottlenecks found: {len(result.bottleneck_report.bottlenecks)}")
        lines.append(f"Critical path length: {result.bottleneck_report.critical_path_length}")
        lines.append(f"Parallelization opportunities: {len(result.bottleneck_report.parallelization_opportunities)}")
        lines.append(f"Estimated improvement: {result.bottleneck_report.estimated_improvement:.1%}")
        lines.append("")

        lines.append("--- LATENCY ANALYSIS ---")
        lines.append(f"Total latency: {result.latency_report.total_ms:.1f}ms")
        lines.append(f"P50: {result.latency_report.p50_ms:.1f}ms")
        lines.append(f"P95: {result.latency_report.p95_ms:.1f}ms")
        lines.append(f"P99: {result.latency_report.p99_ms:.1f}ms")
        if result.latency_report.slowest_nodes:
            lines.append(f"Slowest nodes: {', '.join(result.latency_report.slowest_nodes[:3])}")
        lines.append("")

        lines.append("--- COMPRESSION PROPOSAL ---")
        lines.append(f"Removable edges: {len(result.compression_proposal.removable_edges)}")
        lines.append(f"Mergeable node pairs: {len(result.compression_proposal.mergeable_nodes)}")
        lines.append(f"Parallelizable chains: {len(result.compression_proposal.parallelizable_chains)}")
        lines.append(f"Estimated speedup: {result.compression_proposal.estimated_speedup:.2f}x")
        lines.append("")

        lines.append("--- REDUNDANCY DETECTION ---")
        lines.append(f"Duplicate groups: {len(result.redundancy_report.duplicate_nodes)}")
        lines.append(f"No-op nodes: {len(result.redundancy_report.noop_nodes)}")
        lines.append(f"Dead nodes: {len(result.redundancy_report.dead_nodes)}")
        lines.append(f"Redundancy score: {result.redundancy_report.redundancy_score:.3f}")
        lines.append("")

        if benchmark:
            lines.append("--- BENCHMARK ---")
            lines.append(
                f"Nodes: {benchmark.original_metrics.node_count} → "
                f"{benchmark.optimized_metrics.node_count}"
            )
            lines.append(
                f"Edges: {benchmark.original_metrics.edge_count} → "
                f"{benchmark.optimized_metrics.edge_count}"
            )
            lines.append(
                f"Stages: {benchmark.original_metrics.stage_count} → "
                f"{benchmark.optimized_metrics.stage_count}"
            )
            lines.append(
                f"Max parallelism: {benchmark.original_metrics.max_parallelism} → "
                f"{benchmark.optimized_metrics.max_parallelism}"
            )
            if benchmark.warnings:
                lines.append("Warnings:")
                for w in benchmark.warnings:
                    lines.append(f"  ⚠ {w}")
            lines.append("")

        if result.recommendations:
            lines.append("--- RECOMMENDATIONS ---")
            for rec in result.recommendations:
                lines.append(f"  [{rec.priority}] [{rec.category}] {rec.description}")
                lines.append(f"      Expected: {rec.expected_benefit}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def _build_execution_results(
        self,
        graph: TaskGraph,
        execution_history: list[dict[str, Any]] | None,
    ) -> dict[str, Any] | None:
        """Build execution_results dict from graph state and history."""
        node_durations: dict[str, float] = {}
        node_retries: dict[str, int] = {}

        for node_id, node in graph.nodes.items():
            if node.duration_ms is not None:
                node_durations[node_id] = node.duration_ms
            if node.attempts > 1:
                node_retries[node_id] = node.attempts - 1

        if execution_history:
            for record in execution_history:
                for nid, dur in record.get("node_durations", {}).items():
                    if nid not in node_durations:
                        node_durations[nid] = float(dur)
                for nid, retries in record.get("node_retries", {}).items():
                    current = node_retries.get(nid, 0)
                    node_retries[nid] = max(current, int(retries))

        if not node_durations and not node_retries:
            return None

        return {
            "node_durations": node_durations,
            "node_retries": node_retries,
        }

    def _compute_metrics(self, graph: TaskGraph) -> GraphMetrics:
        """Compute structural metrics for a graph."""
        stages = graph.parallel_stages()
        stage_count = len(stages)
        max_parallelism = max(len(s) for s in stages) if stages else 0

        critical_path = self._compute_critical_path_length(graph)

        estimated_latency = 0.0
        for node in graph.nodes.values():
            if node.duration_ms is not None:
                estimated_latency += node.duration_ms / max(max_parallelism, 1)

        return GraphMetrics(
            node_count=len(graph.nodes),
            edge_count=len(graph.edges),
            stage_count=stage_count,
            critical_path_length=critical_path,
            max_parallelism=max_parallelism,
            estimated_latency_ms=estimated_latency,
        )

    def _compute_critical_path_length(self, graph: TaskGraph) -> int:
        """Compute the length of the longest path in the graph."""
        if not graph.nodes:
            return 0

        topo = graph.topological_order()
        dist: dict[str, int] = {nid: 0 for nid in graph.nodes}

        for node_id in topo:
            for dependent in graph.get_dependents(node_id):
                dist[dependent] = max(dist[dependent], dist[node_id] + 1)

        return max(dist.values()) + 1 if dist else 0

    def _compute_overall_score(
        self,
        bottleneck_report: BottleneckReport,
        latency_report: LatencyReport,
        compression_proposal: CompressionProposal,
        redundancy_report: RedundancyReport,
    ) -> float:
        """
        Compute overall optimization potential score (0 = no optimization needed, 1 = highly optimizable).
        """
        bottleneck_factor = min(0.3, bottleneck_report.estimated_improvement)
        compression_factor = min(0.3, (compression_proposal.estimated_speedup - 1.0) * 0.5)
        redundancy_factor = min(0.2, redundancy_report.redundancy_score * 0.5)

        parallelism_factor = 0.0
        if bottleneck_report.parallelization_opportunities:
            avg_speedup = sum(
                o.speedup_factor for o in bottleneck_report.parallelization_opportunities
            ) / len(bottleneck_report.parallelization_opportunities)
            parallelism_factor = min(0.2, (avg_speedup - 1.0) * 0.15)

        return min(1.0, max(0.0,
            bottleneck_factor + compression_factor + redundancy_factor + parallelism_factor
        ))

    def _generate_recommendations(
        self,
        bottleneck_report: BottleneckReport,
        latency_report: LatencyReport,
        compression_proposal: CompressionProposal,
        redundancy_report: RedundancyReport,
    ) -> list[Recommendation]:
        """Generate prioritized recommendations from all analysis results."""
        recommendations: list[Recommendation] = []
        priority = 1

        critical_bottlenecks = [
            b for b in bottleneck_report.bottlenecks if b.severity > 0.7
        ]
        if critical_bottlenecks:
            recommendations.append(Recommendation(
                priority=priority,
                category="bottleneck",
                description=(
                    f"Address {len(critical_bottlenecks)} high-severity bottlenecks "
                    f"(worst: {critical_bottlenecks[0].description[:80]})"
                ),
                expected_benefit="Reduce critical path blocking and improve throughput",
            ))
            priority += 1

        if redundancy_report.redundancy_score > 0.2:
            recommendations.append(Recommendation(
                priority=priority,
                category="redundancy",
                description=(
                    f"Remove redundant nodes (score={redundancy_report.redundancy_score:.2f}): "
                    f"{len(redundancy_report.noop_nodes)} no-ops, "
                    f"{len(redundancy_report.dead_nodes)} dead nodes"
                ),
                expected_benefit="Simpler graph, fewer wasted resources",
            ))
            priority += 1

        if compression_proposal.removable_edges:
            recommendations.append(Recommendation(
                priority=priority,
                category="compression",
                description=(
                    f"Remove {len(compression_proposal.removable_edges)} "
                    f"transitive dependency edges"
                ),
                expected_benefit="Reduced scheduling overhead, potential parallelism gains",
            ))
            priority += 1

        if compression_proposal.parallelizable_chains:
            best = max(
                compression_proposal.parallelizable_chains,
                key=lambda c: c.estimated_speedup
            )
            recommendations.append(Recommendation(
                priority=priority,
                category="parallelization",
                description=(
                    f"Parallelize {len(compression_proposal.parallelizable_chains)} chains "
                    f"(best speedup: {best.estimated_speedup:.1f}x for "
                    f"{len(best.nodes)} nodes)"
                ),
                expected_benefit=f"Up to {best.estimated_speedup:.1f}x speedup on parallelizable chains",
            ))
            priority += 1

        if latency_report.slowest_nodes:
            recommendations.append(Recommendation(
                priority=priority,
                category="latency",
                description=(
                    f"Optimize slowest nodes: {', '.join(latency_report.slowest_nodes[:3])}"
                ),
                expected_benefit="Direct reduction in end-to-end execution time",
            ))
            priority += 1

        if compression_proposal.mergeable_nodes:
            recommendations.append(Recommendation(
                priority=priority,
                category="merge",
                description=(
                    f"Merge {len(compression_proposal.mergeable_nodes)} node pairs "
                    f"with identical handlers"
                ),
                expected_benefit="Fewer nodes, reduced scheduling overhead",
            ))
            priority += 1

        return recommendations

    def _compute_improvements(
        self, original: GraphMetrics, optimized: GraphMetrics
    ) -> dict[str, Any]:
        """Compute improvement metrics between original and optimized."""
        def pct_change(before: float, after: float) -> float:
            if before == 0:
                return 0.0
            return round((after - before) / before * 100, 1)

        return {
            "nodes_reduced": original.node_count - optimized.node_count,
            "edges_reduced": original.edge_count - optimized.edge_count,
            "stages_reduced": original.stage_count - optimized.stage_count,
            "node_reduction_pct": pct_change(original.node_count, optimized.node_count),
            "edge_reduction_pct": pct_change(original.edge_count, optimized.edge_count),
            "stage_reduction_pct": pct_change(original.stage_count, optimized.stage_count),
            "parallelism_change": optimized.max_parallelism - original.max_parallelism,
            "latency_change_ms": round(
                optimized.estimated_latency_ms - original.estimated_latency_ms, 1
            ),
        }

    def _generate_warnings(
        self,
        original: TaskGraph,
        optimized: TaskGraph,
        improvements: dict[str, Any],
    ) -> list[str]:
        """Generate warnings about potential issues with the optimization."""
        warnings: list[str] = []

        if len(optimized.nodes) < len(original.nodes) * 0.5:
            warnings.append(
                "Optimization removes >50% of nodes — verify semantic correctness"
            )

        if improvements.get("stages_reduced", 0) > len(original.parallel_stages()) * 0.5:
            warnings.append(
                "Significant stage reduction — test for race conditions"
            )

        original_handlers = {n.handler for n in original.nodes.values()}
        optimized_handlers = {n.handler for n in optimized.nodes.values()}
        lost_handlers = original_handlers - optimized_handlers
        if lost_handlers:
            warnings.append(
                f"Handlers removed from graph: {', '.join(sorted(lost_handlers)[:3])}"
            )

        if not optimized.nodes:
            warnings.append("Optimized graph is empty — optimization may be too aggressive")

        return warnings
