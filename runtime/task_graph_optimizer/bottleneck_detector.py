"""
Bottleneck Detector — Detect bottlenecks in DAG execution through static
and dynamic analysis.

Static analysis identifies structural issues (high fan-in, sequential chains).
Dynamic analysis (with execution results) identifies performance issues
(slow nodes, retry-heavy nodes).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from runtime.task_graph.dag import TaskGraph, TaskNode, TaskStatus

logger = logging.getLogger(__name__)


class BottleneckType(str, Enum):
    FAN_IN = "fan_in"
    CRITICAL_PATH = "critical_path"
    SEQUENTIAL_CHAIN = "sequential_chain"
    SLOW_NODE = "slow_node"
    RETRY_HEAVY = "retry_heavy"


@dataclass
class BottleneckInfo:
    """Information about a detected bottleneck."""
    node_id: str
    type: BottleneckType
    severity: float  # 0.0 - 1.0
    description: str
    suggestion: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "type": self.type.value,
            "severity": round(self.severity, 3),
            "description": self.description,
            "suggestion": self.suggestion,
        }


@dataclass
class ParallelizationOpportunity:
    """A chain that could potentially be parallelized."""
    chain: list[str]
    current_sequential_cost: float
    estimated_parallel_cost: float
    speedup_factor: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain": self.chain,
            "current_sequential_cost": round(self.current_sequential_cost, 1),
            "estimated_parallel_cost": round(self.estimated_parallel_cost, 1),
            "speedup_factor": round(self.speedup_factor, 2),
        }


@dataclass
class BottleneckReport:
    """Complete bottleneck analysis report."""
    bottlenecks: list[BottleneckInfo]
    critical_path_length: int
    parallelization_opportunities: list[ParallelizationOpportunity]
    estimated_improvement: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "bottlenecks": [b.to_dict() for b in self.bottlenecks],
            "bottleneck_count": len(self.bottlenecks),
            "critical_path_length": self.critical_path_length,
            "parallelization_opportunities": [
                p.to_dict() for p in self.parallelization_opportunities
            ],
            "estimated_improvement": round(self.estimated_improvement, 3),
        }


class BottleneckDetector:
    """
    Detect bottlenecks in task graph execution.

    Performs both static structural analysis and dynamic performance analysis
    to identify nodes that limit overall throughput.

    Usage:
        detector = BottleneckDetector()
        report = detector.detect(graph)
        report = detector.detect(graph, execution_results=results)
    """

    def __init__(
        self,
        fan_in_threshold: int = 3,
        slow_node_threshold_ms: float = 5000.0,
        retry_threshold: int = 2,
    ):
        self._fan_in_threshold = fan_in_threshold
        self._slow_node_threshold = slow_node_threshold_ms
        self._retry_threshold = retry_threshold

    def detect(
        self,
        graph: TaskGraph,
        execution_results: dict[str, Any] | None = None,
    ) -> BottleneckReport:
        """
        Analyze a TaskGraph for bottlenecks.

        Performs static analysis on graph structure and optionally dynamic
        analysis if execution results are provided.
        """
        bottlenecks: list[BottleneckInfo] = []

        bottlenecks.extend(self._detect_fan_in(graph))
        critical_path = self._compute_critical_path(graph)
        bottlenecks.extend(self._detect_critical_path_bottlenecks(graph, critical_path))
        sequential_chains = self._detect_sequential_chains(graph)

        if execution_results:
            bottlenecks.extend(self._detect_slow_nodes(graph, execution_results))
            bottlenecks.extend(self._detect_retry_heavy(graph, execution_results))

        parallelization_ops = self._find_parallelization_opportunities(
            graph, sequential_chains, execution_results
        )

        estimated_improvement = self._estimate_overall_improvement(
            bottlenecks, parallelization_ops
        )

        bottlenecks.sort(key=lambda b: b.severity, reverse=True)

        report = BottleneckReport(
            bottlenecks=bottlenecks,
            critical_path_length=len(critical_path),
            parallelization_opportunities=parallelization_ops,
            estimated_improvement=estimated_improvement,
        )

        logger.info(
            "Detected %d bottlenecks, %d parallelization opportunities",
            len(bottlenecks), len(parallelization_ops)
        )
        return report

    def _detect_fan_in(self, graph: TaskGraph) -> list[BottleneckInfo]:
        """Detect nodes with high fan-in (many dependencies)."""
        bottlenecks: list[BottleneckInfo] = []

        for node_id in graph.nodes:
            deps = graph.get_dependencies(node_id)
            if len(deps) >= self._fan_in_threshold:
                severity = min(1.0, len(deps) / (self._fan_in_threshold * 2))
                bottlenecks.append(BottleneckInfo(
                    node_id=node_id,
                    type=BottleneckType.FAN_IN,
                    severity=severity,
                    description=(
                        f"Node '{node_id}' has {len(deps)} dependencies — "
                        f"it cannot start until all complete"
                    ),
                    suggestion=(
                        "Consider splitting dependencies into stages or "
                        "reducing mandatory dependencies"
                    ),
                ))

        return bottlenecks

    def _compute_critical_path(self, graph: TaskGraph) -> list[str]:
        """Compute the longest path through the graph (critical path)."""
        if not graph.nodes:
            return []

        topo_order = graph.topological_order()
        dist: dict[str, int] = {nid: 0 for nid in graph.nodes}
        parent: dict[str, str | None] = {nid: None for nid in graph.nodes}

        for node_id in topo_order:
            for dependent in graph.get_dependents(node_id):
                if dist[node_id] + 1 > dist[dependent]:
                    dist[dependent] = dist[node_id] + 1
                    parent[dependent] = node_id

        if not dist:
            return []

        end_node = max(dist, key=lambda k: dist[k])
        path: list[str] = []
        current: str | None = end_node
        while current is not None:
            path.append(current)
            current = parent[current]
        path.reverse()
        return path

    def _detect_critical_path_bottlenecks(
        self, graph: TaskGraph, critical_path: list[str]
    ) -> list[BottleneckInfo]:
        """Mark nodes on the critical path as potential bottlenecks."""
        bottlenecks: list[BottleneckInfo] = []

        if len(critical_path) <= 2:
            return bottlenecks

        total_nodes = len(graph.nodes)
        path_ratio = len(critical_path) / max(total_nodes, 1)

        if path_ratio > 0.5:
            for node_id in critical_path:
                bottlenecks.append(BottleneckInfo(
                    node_id=node_id,
                    type=BottleneckType.CRITICAL_PATH,
                    severity=path_ratio * 0.7,
                    description=(
                        f"Node '{node_id}' is on the critical path "
                        f"({len(critical_path)}/{total_nodes} nodes)"
                    ),
                    suggestion=(
                        "Optimize this node's execution time or find ways to "
                        "parallelize adjacent nodes off the critical path"
                    ),
                ))

        return bottlenecks

    def _detect_sequential_chains(self, graph: TaskGraph) -> list[list[str]]:
        """Find sequential chains (A→B→C where each has exactly one dep/dependent)."""
        chains: list[list[str]] = []
        visited: set[str] = set()

        for node_id in graph.nodes:
            if node_id in visited:
                continue

            deps = graph.get_dependencies(node_id)
            if len(deps) != 0:
                continue

            chain = self._follow_chain(graph, node_id)
            if len(chain) >= 3:
                chains.append(chain)
                visited.update(chain)

        return chains

    def _follow_chain(self, graph: TaskGraph, start: str) -> list[str]:
        """Follow a linear chain from a starting node."""
        chain = [start]
        current = start

        while True:
            dependents = graph.get_dependents(current)
            if len(dependents) != 1:
                break
            next_node = dependents[0]
            deps_of_next = graph.get_dependencies(next_node)
            if len(deps_of_next) != 1:
                break
            chain.append(next_node)
            current = next_node

        return chain

    def _detect_slow_nodes(
        self, graph: TaskGraph, execution_results: dict[str, Any]
    ) -> list[BottleneckInfo]:
        """Detect nodes with long execution duration (dynamic analysis)."""
        bottlenecks: list[BottleneckInfo] = []
        node_durations = execution_results.get("node_durations", {})

        for node_id, duration_ms in node_durations.items():
            if node_id not in graph.nodes:
                continue
            if duration_ms > self._slow_node_threshold:
                severity = min(1.0, duration_ms / (self._slow_node_threshold * 3))
                bottlenecks.append(BottleneckInfo(
                    node_id=node_id,
                    type=BottleneckType.SLOW_NODE,
                    severity=severity,
                    description=(
                        f"Node '{node_id}' took {duration_ms:.0f}ms "
                        f"(threshold: {self._slow_node_threshold:.0f}ms)"
                    ),
                    suggestion=(
                        "Profile this task's handler for optimization opportunities "
                        "or consider breaking into smaller parallel subtasks"
                    ),
                ))

        return bottlenecks

    def _detect_retry_heavy(
        self, graph: TaskGraph, execution_results: dict[str, Any]
    ) -> list[BottleneckInfo]:
        """Detect nodes with excessive retries (dynamic analysis)."""
        bottlenecks: list[BottleneckInfo] = []
        node_retries = execution_results.get("node_retries", {})

        for node_id, retry_count in node_retries.items():
            if node_id not in graph.nodes:
                continue
            if retry_count >= self._retry_threshold:
                severity = min(1.0, retry_count / 5.0)
                bottlenecks.append(BottleneckInfo(
                    node_id=node_id,
                    type=BottleneckType.RETRY_HEAVY,
                    severity=severity,
                    description=(
                        f"Node '{node_id}' required {retry_count} retries"
                    ),
                    suggestion=(
                        "Investigate root cause of failures; consider adding "
                        "pre-condition checks or improving error handling"
                    ),
                ))

        return bottlenecks

    def _find_parallelization_opportunities(
        self,
        graph: TaskGraph,
        sequential_chains: list[list[str]],
        execution_results: dict[str, Any] | None,
    ) -> list[ParallelizationOpportunity]:
        """Identify sequential chains that could potentially be parallelized."""
        opportunities: list[ParallelizationOpportunity] = []
        node_durations = {}
        if execution_results:
            node_durations = execution_results.get("node_durations", {})

        for chain in sequential_chains:
            if len(chain) < 3:
                continue

            durations = [
                node_durations.get(nid, 1000.0) for nid in chain
            ]
            sequential_cost = sum(durations)
            parallel_cost = max(durations) + sum(sorted(durations)[:-1]) * 0.3
            speedup = sequential_cost / max(parallel_cost, 1)

            if speedup > 1.2:
                opportunities.append(ParallelizationOpportunity(
                    chain=chain,
                    current_sequential_cost=sequential_cost,
                    estimated_parallel_cost=parallel_cost,
                    speedup_factor=speedup,
                ))

        opportunities.sort(key=lambda o: o.speedup_factor, reverse=True)
        return opportunities

    def _estimate_overall_improvement(
        self,
        bottlenecks: list[BottleneckInfo],
        parallelization_ops: list[ParallelizationOpportunity],
    ) -> float:
        """Estimate potential improvement as a fraction (0-1)."""
        if not bottlenecks and not parallelization_ops:
            return 0.0

        bottleneck_factor = min(0.3, sum(b.severity for b in bottlenecks) * 0.05)

        parallel_factor = 0.0
        if parallelization_ops:
            avg_speedup = sum(o.speedup_factor for o in parallelization_ops) / len(parallelization_ops)
            parallel_factor = min(0.5, (avg_speedup - 1.0) * 0.3)

        return min(1.0, bottleneck_factor + parallel_factor)
