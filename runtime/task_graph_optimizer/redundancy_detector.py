"""
Redundancy Detector — Detect redundant and unnecessary nodes in a task graph.

Identifies duplicate nodes (same handler), no-op nodes (always skip),
dead nodes (no path to terminal), and nodes that produce identical results.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from runtime.task_graph.dag import TaskGraph, TaskNode, TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class DuplicateNodeGroup:
    """A group of nodes that appear to be duplicates."""
    handler: str
    node_ids: list[str]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "handler": self.handler,
            "node_ids": self.node_ids,
            "reason": self.reason,
        }


@dataclass
class NoopNode:
    """A node that always results in skip or produces no meaningful output."""
    node_id: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "reason": self.reason,
        }


@dataclass
class DeadNode:
    """A node with no path to any terminal node in the graph."""
    node_id: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "reason": self.reason,
        }


@dataclass
class RedundancyReport:
    """Complete redundancy analysis report."""
    duplicate_nodes: list[DuplicateNodeGroup]
    noop_nodes: list[NoopNode]
    dead_nodes: list[DeadNode]
    redundancy_score: float

    def to_dict(self) -> dict[str, Any]:
        total_issues = (
            sum(len(g.node_ids) - 1 for g in self.duplicate_nodes)
            + len(self.noop_nodes)
            + len(self.dead_nodes)
        )
        return {
            "duplicate_nodes": [d.to_dict() for d in self.duplicate_nodes],
            "noop_nodes": [n.to_dict() for n in self.noop_nodes],
            "dead_nodes": [d.to_dict() for d in self.dead_nodes],
            "redundancy_score": round(self.redundancy_score, 3),
            "total_redundant_nodes": total_issues,
        }


class RedundancyDetector:
    """
    Detect redundant and unnecessary nodes in a task graph.

    Identifies:
      - Duplicate nodes: same handler with identical parameters
      - No-op nodes: always skip or produce no result
      - Dead nodes: disconnected from any useful output path

    Usage:
        detector = RedundancyDetector()
        report = detector.detect(graph)
        print(f"Redundancy score: {report.redundancy_score:.2f}")
    """

    def detect(self, graph: TaskGraph) -> RedundancyReport:
        """
        Find redundant/duplicate nodes in the graph.

        Performs structural analysis to identify nodes that can be removed
        without affecting the graph's overall output.
        """
        duplicates = self._find_duplicate_nodes(graph)
        noops = self._find_noop_nodes(graph)
        dead = self._find_dead_nodes(graph)

        redundancy_score = self._compute_redundancy_score(
            graph, duplicates, noops, dead
        )

        report = RedundancyReport(
            duplicate_nodes=duplicates,
            noop_nodes=noops,
            dead_nodes=dead,
            redundancy_score=redundancy_score,
        )

        logger.info(
            "Redundancy detection: %d duplicate groups, %d no-ops, %d dead nodes, score=%.3f",
            len(duplicates), len(noops), len(dead), redundancy_score
        )
        return report

    def _find_duplicate_nodes(self, graph: TaskGraph) -> list[DuplicateNodeGroup]:
        """
        Find nodes with identical handlers and parameters.

        Nodes are considered duplicates if they have the same handler and
        the same parameters — they would produce identical results.
        """
        handler_groups: dict[str, list[str]] = {}

        for node_id, node in graph.nodes.items():
            key = self._node_signature(node)
            if key not in handler_groups:
                handler_groups[key] = []
            handler_groups[key].append(node_id)

        duplicates: list[DuplicateNodeGroup] = []
        for key, node_ids in handler_groups.items():
            if len(node_ids) < 2:
                continue

            handler = graph.nodes[node_ids[0]].handler
            duplicates.append(DuplicateNodeGroup(
                handler=handler,
                node_ids=node_ids,
                reason=(
                    f"Nodes share handler '{handler}' with identical parameters — "
                    f"may produce duplicate results"
                ),
            ))

        return duplicates

    def _find_noop_nodes(self, graph: TaskGraph) -> list[NoopNode]:
        """
        Find nodes that always skip or have been consistently skipped.

        A node is considered a no-op if:
          - It's already in SKIPPED status
          - It has no handler (empty handler string)
          - Its result is always None/empty after completion
        """
        noops: list[NoopNode] = []

        for node_id, node in graph.nodes.items():
            if node.status == TaskStatus.SKIPPED:
                noops.append(NoopNode(
                    node_id=node_id,
                    reason=f"Node is in SKIPPED state: {node.error or 'no reason'}",
                ))
            elif not node.handler or node.handler.strip() == "":
                noops.append(NoopNode(
                    node_id=node_id,
                    reason="Node has no handler defined — will never produce output",
                ))
            elif node.status == TaskStatus.COMPLETED and node.result is None:
                dependents = graph.get_dependents(node_id)
                if not dependents:
                    noops.append(NoopNode(
                        node_id=node_id,
                        reason="Completed with no result and no dependents — effectively a no-op",
                    ))

        return noops

    def _find_dead_nodes(self, graph: TaskGraph) -> list[DeadNode]:
        """
        Find nodes with no path to any terminal node.

        A terminal node is one with no dependents (leaf node). A dead node
        is one that cannot reach any terminal and is itself not terminal.
        """
        if not graph.nodes:
            return []

        terminal_nodes = {
            nid for nid in graph.nodes
            if not graph.get_dependents(nid)
        }

        reachable_from: dict[str, set[str]] = {nid: set() for nid in graph.nodes}
        for nid in graph.nodes:
            visited: set[str] = set()
            queue = [nid]
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                reachable_from[nid].add(current)
                queue.extend(graph.get_dependents(current))

        dead: list[DeadNode] = []
        for node_id in graph.nodes:
            if node_id in terminal_nodes:
                continue

            can_reach_terminal = any(
                t in reachable_from[node_id] for t in terminal_nodes
            )
            if not can_reach_terminal:
                deps_of = graph.get_dependencies(node_id)
                if not deps_of and not graph.get_dependents(node_id):
                    dead.append(DeadNode(
                        node_id=node_id,
                        reason="Isolated node — no dependencies and no dependents",
                    ))
                elif not can_reach_terminal:
                    dead.append(DeadNode(
                        node_id=node_id,
                        reason="No path from this node reaches any terminal (leaf) node",
                    ))

        return dead

    def _node_signature(self, node: TaskNode) -> str:
        """Create a signature string for duplicate detection."""
        import json
        params_str = json.dumps(node.params, sort_keys=True, default=str)
        return f"{node.handler}|{params_str}"

    def _compute_redundancy_score(
        self,
        graph: TaskGraph,
        duplicates: list[DuplicateNodeGroup],
        noops: list[NoopNode],
        dead: list[DeadNode],
    ) -> float:
        """
        Compute overall redundancy score (0 = no redundancy, 1 = fully redundant).

        Based on the ratio of redundant nodes to total nodes.
        """
        total = len(graph.nodes)
        if total == 0:
            return 0.0

        redundant_count = (
            sum(len(g.node_ids) - 1 for g in duplicates)
            + len(noops)
            + len(dead)
        )

        return min(1.0, redundant_count / total)
