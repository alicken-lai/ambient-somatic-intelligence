"""Truth graph — registry of nodes, edges, and integrity checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kernel.truth.truth_edge import EdgeKind, TruthEdge
from kernel.truth.truth_node import TruthNode
from kernel.truth.truth_validator import TruthValidator, ValidationResult


@dataclass
class ConflictReport:
    node_id: str
    conflict_type: str
    detail: str


@dataclass
class ChecksumReport:
    node_id: str
    expected: str
    actual: str
    valid: bool


class TruthGraph:
    """
    Central graph of auditable truth nodes.

    No hidden truth: all nodes are indexed by id with full provenance.
    """

    def __init__(self, validator: TruthValidator | None = None) -> None:
        self.nodes: dict[str, TruthNode] = {}
        self.edges: list[TruthEdge] = []
        self._validator = validator or TruthValidator()

    def register_node(self, node: TruthNode) -> ValidationResult:
        """Register a truth node after validation."""
        result = self._validator.validate_registration(node, self)
        if not result.valid:
            return result
        self.nodes[node.id] = node
        return result

    def add_edge(self, edge: TruthEdge) -> ValidationResult:
        """Add a dependency edge after validation."""
        result = self._validator.validate_edge(edge, self)
        if not result.valid:
            return result
        self.edges.append(edge)
        return result

    def get_node(self, node_id: str) -> TruthNode | None:
        return self.nodes.get(node_id)

    def detect_conflicts(self) -> list[ConflictReport]:
        """
        Detect version/checksum conflicts and circular dependencies.

        Returns a list of detected conflicts (empty if graph is consistent).
        """
        conflicts: list[ConflictReport] = []
        seen_versions: dict[str, set[str]] = {}

        for node_id, node in self.nodes.items():
            versions = seen_versions.setdefault(node_id, set())
            key = f"{node.version}:{node.checksum}"
            if key in versions:
                conflicts.append(
                    ConflictReport(
                        node_id=node_id,
                        conflict_type="duplicate_version",
                        detail=f"duplicate version/checksum entry for {node_id}",
                    )
                )
            versions.add(key)
            if not node.verify_checksum():
                conflicts.append(
                    ConflictReport(
                        node_id=node_id,
                        conflict_type="checksum_invalid",
                        detail="stored checksum does not match payload",
                    )
                )

        # Simple cycle detection via DFS
        adjacency: dict[str, list[str]] = {}
        for edge in self.edges:
            if edge.kind in (EdgeKind.DEPENDS_ON, EdgeKind.DERIVES_FROM):
                adjacency.setdefault(edge.source_id, []).append(edge.target_id)

        visited: set[str] = set()
        stack: set[str] = set()

        def dfs(node_id: str) -> bool:
            if node_id in stack:
                return True
            if node_id in visited:
                return False
            visited.add(node_id)
            stack.add(node_id)
            for target in adjacency.get(node_id, []):
                if dfs(target):
                    return True
            stack.remove(node_id)
            return False

        for node_id in self.nodes:
            if dfs(node_id):
                conflicts.append(
                    ConflictReport(
                        node_id=node_id,
                        conflict_type="circular_dependency",
                        detail=f"cycle detected involving {node_id}",
                    )
                )
                break

        return conflicts

    def stale_sources(self) -> list[str]:
        """Return node ids whose timestamps exceed the staleness threshold."""
        return [
            node_id
            for node_id, node in self.nodes.items()
            if self._validator.is_stale(node)
        ]

    def validate_checksums(self) -> list[ChecksumReport]:
        """Verify all node payloads against stored checksums."""
        reports: list[ChecksumReport] = []
        for node_id, node in self.nodes.items():
            actual = TruthNode.compute_checksum(node.payload)
            reports.append(
                ChecksumReport(
                    node_id=node_id,
                    expected=node.checksum,
                    actual=actual,
                    valid=node.checksum == actual,
                )
            )
        return reports

    def stats(self) -> dict[str, Any]:
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "conflicts": len(self.detect_conflicts()),
            "stale_count": len(self.stale_sources()),
        }
