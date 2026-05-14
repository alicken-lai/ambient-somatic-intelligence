"""
Dependency Graph — Runtime dependency analysis between subsystems.

Extracts dependency edges from import analysis and provides cycle detection,
critical path analysis, and dependency depth calculation using DFS/BFS
algorithms on the adjacency structure.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from identity.cognitive_self_model.architecture_graph import ArchitectureGraph

logger = logging.getLogger("identity.cognitive_self_model.dependency_graph")


@dataclass
class DependencyEdge:
    """A directed dependency from one subsystem to another."""
    source: str
    target: str
    via: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "via": self.via,
        }


@dataclass
class CyclePath:
    """A detected circular dependency chain."""
    path: list[str]
    length: int = 0

    def __post_init__(self):
        self.length = len(self.path)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "length": self.length,
            "cycle_str": " → ".join(self.path),
        }


class DependencyGraph:
    """
    Analyzes runtime dependencies between subsystems.

    Uses the ArchitectureGraph's import analysis to build an adjacency list
    and detect structural issues like circular dependencies or overly deep
    dependency chains.
    """

    def __init__(self):
        self._adjacency: dict[str, set[str]] = defaultdict(set)
        self._edges: list[DependencyEdge] = []
        self._all_subsystems: set[str] = set()
        self._built = False

    def build_from_architecture(self, arch_graph: "ArchitectureGraph") -> "DependencyGraph":
        """Extract dependency edges from import analysis in the architecture graph."""
        topology = arch_graph.get_system_topology()

        self._adjacency = defaultdict(set)
        self._edges = []
        self._all_subsystems = set()

        for subsystem_name, subsystem_data in topology["subsystems"].items():
            self._all_subsystems.add(subsystem_name)
            for dep in subsystem_data.get("dependencies", []):
                self._all_subsystems.add(dep)
                self._adjacency[subsystem_name].add(dep)

        edge_map: dict[tuple[str, str], list[str]] = defaultdict(list)
        for edge in topology.get("edges", []):
            key = (edge["from"], edge["to"])
            edge_map[key].append(edge.get("via", ""))

        for (src, tgt), via_list in edge_map.items():
            self._edges.append(DependencyEdge(source=src, target=tgt, via=via_list))

        self._built = True
        logger.info(
            "Dependency graph built: %d subsystems, %d edges",
            len(self._all_subsystems),
            len(self._edges),
        )
        return self

    def get_runtime_dependencies(self) -> dict[str, list[str]]:
        """Return the dependency adjacency list."""
        self._ensure_built()
        return {k: sorted(v) for k, v in self._adjacency.items()}

    def find_circular_dependencies(self) -> list[CyclePath]:
        """Detect cycles using DFS with back-edge detection."""
        self._ensure_built()
        cycles: list[CyclePath] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._adjacency.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(CyclePath(path=cycle))

            path.pop()
            rec_stack.discard(node)

        for node in sorted(self._all_subsystems):
            if node not in visited:
                dfs(node)

        return cycles

    def get_dependency_depth(self, subsystem: str) -> int:
        """Calculate how deep a subsystem is in the dependency tree (longest incoming chain)."""
        self._ensure_built()
        if subsystem not in self._all_subsystems:
            return -1

        reverse_adj: dict[str, set[str]] = defaultdict(set)
        for src, targets in self._adjacency.items():
            for tgt in targets:
                reverse_adj[tgt].add(src)

        visited: set[str] = set()
        max_depth = 0

        def dfs_depth(node: str, depth: int) -> None:
            nonlocal max_depth
            visited.add(node)
            max_depth = max(max_depth, depth)

            for parent in reverse_adj.get(node, set()):
                if parent not in visited:
                    dfs_depth(parent, depth + 1)

            visited.discard(node)

        dfs_depth(subsystem, 0)
        return max_depth

    def get_critical_path(self) -> list[str]:
        """Find the subsystems on the longest dependency chain."""
        self._ensure_built()

        longest_path: list[str] = []

        def dfs(node: str, path: list[str], visited: set[str]) -> None:
            nonlocal longest_path
            path.append(node)
            visited.add(node)

            if len(path) > len(longest_path):
                longest_path = path[:]

            for neighbor in self._adjacency.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path, visited)

            path.pop()
            visited.discard(node)

        for node in sorted(self._all_subsystems):
            dfs(node, [], set())

        return longest_path

    def to_mermaid(self) -> str:
        """Generate a Mermaid dependency diagram."""
        self._ensure_built()
        lines = ["graph LR"]

        for subsystem in sorted(self._all_subsystems):
            safe_id = subsystem.replace(".", "_")
            lines.append(f"    {safe_id}[{subsystem}]")

        seen: set[tuple[str, str]] = set()
        for edge in self._edges:
            from_id = edge.source.replace(".", "_")
            to_id = edge.target.replace(".", "_")
            pair = (from_id, to_id)
            if pair not in seen:
                seen.add(pair)
                lines.append(f"    {from_id} --> {to_id}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Serializable representation of the dependency graph."""
        self._ensure_built()
        cycles = self.find_circular_dependencies()
        critical = self.get_critical_path()

        return {
            "subsystems": sorted(self._all_subsystems),
            "adjacency": self.get_runtime_dependencies(),
            "edges": [e.to_dict() for e in self._edges],
            "cycles": [c.to_dict() for c in cycles],
            "critical_path": critical,
            "depths": {
                s: self.get_dependency_depth(s)
                for s in sorted(self._all_subsystems)
            },
        }

    def _ensure_built(self) -> None:
        if not self._built:
            raise RuntimeError(
                "DependencyGraph not built. Call build_from_architecture() first."
            )
