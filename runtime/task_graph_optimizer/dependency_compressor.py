"""
Dependency Compressor — Find opportunities to compress and simplify
dependency chains in task graphs.

Detects transitive dependencies that can be removed, nodes that can be
merged, and sequential chains that could be parallelized.
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from typing import Any

from runtime.task_graph.dag import TaskGraph, TaskEdge, TaskNode, TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class RemovableEdge:
    """An edge that is transitively implied and can be removed."""
    source: str
    target: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "reason": self.reason,
        }


@dataclass
class MergeableNodePair:
    """Two nodes that could potentially be merged into one."""
    node_a: str
    node_b: str
    reason: str
    estimated_savings_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_a": self.node_a,
            "node_b": self.node_b,
            "reason": self.reason,
            "estimated_savings_ms": round(self.estimated_savings_ms, 1),
        }


@dataclass
class ParallelizableChain:
    """A sequential chain that could potentially be executed in parallel."""
    nodes: list[str]
    current_depth: int
    proposed_depth: int
    estimated_speedup: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": self.nodes,
            "current_depth": self.current_depth,
            "proposed_depth": self.proposed_depth,
            "estimated_speedup": round(self.estimated_speedup, 2),
        }


@dataclass
class CompressionProposal:
    """A complete dependency compression proposal."""
    removable_edges: list[RemovableEdge]
    mergeable_nodes: list[MergeableNodePair]
    parallelizable_chains: list[ParallelizableChain]
    estimated_speedup: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "removable_edges": [e.to_dict() for e in self.removable_edges],
            "mergeable_nodes": [m.to_dict() for m in self.mergeable_nodes],
            "parallelizable_chains": [p.to_dict() for p in self.parallelizable_chains],
            "estimated_speedup": round(self.estimated_speedup, 3),
        }


@dataclass
class CompressionMetrics:
    """Metrics comparing original and compressed graphs."""
    original_nodes: int
    original_edges: int
    original_stages: int
    compressed_nodes: int
    compressed_edges: int
    compressed_stages: int
    nodes_removed: int
    edges_removed: int
    stages_saved: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_nodes": self.original_nodes,
            "original_edges": self.original_edges,
            "original_stages": self.original_stages,
            "compressed_nodes": self.compressed_nodes,
            "compressed_edges": self.compressed_edges,
            "compressed_stages": self.compressed_stages,
            "nodes_removed": self.nodes_removed,
            "edges_removed": self.edges_removed,
            "stages_saved": self.stages_saved,
        }


class DependencyCompressor:
    """
    Find opportunities to compress and simplify dependency chains.

    Analyzes graph structure to detect redundant edges, mergeable nodes,
    and parallelization opportunities without changing semantics.

    Usage:
        compressor = DependencyCompressor()
        proposal = compressor.analyze(graph)
        optimized, metrics = compressor.simulate_compression(graph, proposal)
    """

    def analyze(self, graph: TaskGraph) -> CompressionProposal:
        """
        Analyze a graph for compression opportunities.

        Returns a CompressionProposal describing what can be simplified
        without changing execution semantics.
        """
        removable = self._find_transitive_edges(graph)
        mergeable = self._find_mergeable_nodes(graph)
        parallelizable = self._find_parallelizable_chains(graph)

        estimated_speedup = self._estimate_speedup(
            graph, removable, mergeable, parallelizable
        )

        proposal = CompressionProposal(
            removable_edges=removable,
            mergeable_nodes=mergeable,
            parallelizable_chains=parallelizable,
            estimated_speedup=estimated_speedup,
        )

        logger.info(
            "Compression analysis: %d removable edges, %d mergeable pairs, "
            "%d parallelizable chains, estimated speedup=%.2f",
            len(removable), len(mergeable), len(parallelizable), estimated_speedup
        )
        return proposal

    def simulate_compression(
        self, graph: TaskGraph, proposal: CompressionProposal
    ) -> tuple[TaskGraph, CompressionMetrics]:
        """
        Create a new graph with proposed compressions applied.

        Does NOT modify the original graph. Returns the optimized candidate
        and comparison metrics.
        """
        original_stages = len(graph.parallel_stages())
        original_edges = len(graph.edges)
        original_nodes = len(graph.nodes)

        optimized = TaskGraph(name=f"{graph.name}_optimized", graph_id=f"{graph.id}_opt")
        optimized.metadata = {**graph.metadata, "compressed_from": graph.id}

        for node_id, node in graph.nodes.items():
            optimized.add_task(
                task_id=node_id,
                handler=node.handler,
                name=node.name,
                params=dict(node.params),
                metadata=dict(node.metadata),
            )

        removable_set = {
            (e.source, e.target) for e in proposal.removable_edges
        }
        for edge in graph.edges:
            if (edge.source, edge.target) not in removable_set:
                try:
                    optimized.add_edge(edge.source, edge.target, edge.condition)
                except ValueError:
                    pass

        merged_nodes: set[str] = set()
        for merge in proposal.mergeable_nodes:
            if merge.node_b in optimized.nodes and merge.node_b not in merged_nodes:
                self._merge_node_into(optimized, merge.node_a, merge.node_b)
                merged_nodes.add(merge.node_b)

        compressed_stages = len(optimized.parallel_stages())

        metrics = CompressionMetrics(
            original_nodes=original_nodes,
            original_edges=original_edges,
            original_stages=original_stages,
            compressed_nodes=len(optimized.nodes),
            compressed_edges=len(optimized.edges),
            compressed_stages=compressed_stages,
            nodes_removed=original_nodes - len(optimized.nodes),
            edges_removed=original_edges - len(optimized.edges),
            stages_saved=original_stages - compressed_stages,
        )

        return optimized, metrics

    def _find_transitive_edges(self, graph: TaskGraph) -> list[RemovableEdge]:
        """
        Find edges that are transitively implied.

        If A→B→C and A→C both exist, the edge A→C is redundant because
        C already transitively depends on A through B.
        """
        removable: list[RemovableEdge] = []
        reachable = self._compute_transitive_closure(graph)

        for edge in graph.edges:
            other_paths = False
            for mid_node in graph.nodes:
                if mid_node == edge.source or mid_node == edge.target:
                    continue
                if (
                    mid_node in reachable.get(edge.source, set())
                    and edge.target in reachable.get(mid_node, set())
                ):
                    other_paths = True
                    break

            if other_paths:
                removable.append(RemovableEdge(
                    source=edge.source,
                    target=edge.target,
                    reason=f"Transitive: {edge.source} can reach {edge.target} through intermediate nodes",
                ))

        return removable

    def _find_mergeable_nodes(self, graph: TaskGraph) -> list[MergeableNodePair]:
        """
        Find nodes that could potentially be merged.

        Candidates: nodes with the same handler that are in sequence
        (A→B where both have the same handler).
        """
        mergeable: list[MergeableNodePair] = []

        for edge in graph.edges:
            source_node = graph.nodes[edge.source]
            target_node = graph.nodes[edge.target]

            if source_node.handler != target_node.handler:
                continue

            source_deps = graph.get_dependents(edge.source)
            target_deps = graph.get_dependencies(edge.target)
            if len(source_deps) == 1 and len(target_deps) == 1:
                mergeable.append(MergeableNodePair(
                    node_a=edge.source,
                    node_b=edge.target,
                    reason=(
                        f"Same handler '{source_node.handler}' in direct sequence "
                        f"with no other connections"
                    ),
                    estimated_savings_ms=50.0,
                ))

        return mergeable

    def _find_parallelizable_chains(self, graph: TaskGraph) -> list[ParallelizableChain]:
        """
        Find sequential chains where nodes have no true data dependencies.

        These are chains where parallelism might be safe if the nodes don't
        actually share state.
        """
        parallelizable: list[ParallelizableChain] = []
        visited: set[str] = set()

        for node_id in graph.topological_order():
            if node_id in visited:
                continue

            chain = self._trace_linear_chain(graph, node_id)
            if len(chain) < 3:
                continue

            visited.update(chain)

            handlers = [graph.nodes[nid].handler for nid in chain]
            unique_handlers = set(handlers)
            if len(unique_handlers) > 1:
                parallelizable.append(ParallelizableChain(
                    nodes=chain,
                    current_depth=len(chain),
                    proposed_depth=max(2, len(chain) // 2),
                    estimated_speedup=len(chain) / max(2, len(chain) // 2),
                ))

        return parallelizable

    def _trace_linear_chain(self, graph: TaskGraph, start: str) -> list[str]:
        """Trace a linear chain from a starting node."""
        chain = [start]
        current = start

        while True:
            dependents = graph.get_dependents(current)
            if len(dependents) != 1:
                break
            next_node = dependents[0]
            if len(graph.get_dependencies(next_node)) != 1:
                break
            chain.append(next_node)
            current = next_node

        return chain

    def _compute_transitive_closure(self, graph: TaskGraph) -> dict[str, set[str]]:
        """Compute transitive closure using BFS from each node."""
        closure: dict[str, set[str]] = {nid: set() for nid in graph.nodes}

        for start in graph.nodes:
            queue = list(graph.get_dependents(start))
            visited: set[str] = set()
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                closure[start].add(current)
                queue.extend(graph.get_dependents(current))

        return closure

    def _merge_node_into(self, graph: TaskGraph, target: str, to_remove: str) -> None:
        """Merge to_remove node into target node, updating edges."""
        if to_remove not in graph.nodes:
            return

        for edge in list(graph.edges):
            if edge.target == to_remove:
                if edge.source != target:
                    try:
                        graph.add_edge(edge.source, target, edge.condition)
                    except ValueError:
                        pass
            elif edge.source == to_remove:
                if edge.target != target:
                    try:
                        graph.add_edge(target, edge.target, edge.condition)
                    except ValueError:
                        pass

        graph.edges = [
            e for e in graph.edges
            if e.source != to_remove and e.target != to_remove
        ]
        del graph.nodes[to_remove]

    def _estimate_speedup(
        self,
        graph: TaskGraph,
        removable: list[RemovableEdge],
        mergeable: list[MergeableNodePair],
        parallelizable: list[ParallelizableChain],
    ) -> float:
        """Estimate overall speedup from proposed compressions."""
        total_nodes = len(graph.nodes)
        if total_nodes == 0:
            return 1.0

        edge_factor = len(removable) * 0.02
        merge_factor = len(mergeable) * 0.05

        parallel_factor = 0.0
        for chain in parallelizable:
            parallel_factor += (chain.estimated_speedup - 1.0) * 0.1

        return 1.0 + min(0.5, edge_factor + merge_factor + parallel_factor)
