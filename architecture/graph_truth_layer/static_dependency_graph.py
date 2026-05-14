"""
Static Dependency Graph — AST-based import analysis for the entire codebase.

Parses all Python files to build the actual import dependency graph without
executing any code. Provides cycle detection, external dependency enumeration,
and a full adjacency-list representation of module dependencies.
"""

from __future__ import annotations

import ast
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("architecture.graph_truth_layer.static_dependency_graph")

SKIP_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules", ".mypy_cache", ".pytest_cache"}

KNOWN_TOP_LEVEL_PACKAGES = {
    "kernel", "agents", "governance", "memory", "context",
    "runtime", "somatic", "observability", "identity",
    "architecture", "scripts", "tools",
}


@dataclass
class ImportEdge:
    """A single import relationship between two modules."""
    source_module: str
    target_module: str
    import_type: str
    line_number: int
    is_type_checking: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source_module,
            "target": self.target_module,
            "type": self.import_type,
            "line": self.line_number,
            "type_checking_only": self.is_type_checking,
        }


@dataclass
class DependencyReport:
    """Complete result of a static dependency analysis."""
    edges: list[ImportEdge] = field(default_factory=list)
    cycles: list[list[str]] = field(default_factory=list)
    external_deps: set[str] = field(default_factory=set)
    module_count: int = 0
    edge_count: int = 0
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_count": self.module_count,
            "edge_count": self.edge_count,
            "cycle_count": len(self.cycles),
            "cycles": self.cycles,
            "external_dep_count": len(self.external_deps),
            "external_deps": sorted(self.external_deps),
            "generated_at": self.generated_at,
        }


class StaticDependencyGraph:
    """
    AST-based static analysis of all Python files to build the actual
    import dependency graph. Works standalone without any kernel dependency.
    """

    def __init__(self, root_dir: Path):
        self._root = root_dir.resolve()
        self._edges: list[ImportEdge] = []
        self._graph: dict[str, set[str]] = defaultdict(set)
        self._all_modules: set[str] = set()
        self._external_deps: set[str] = set()
        self._built = False

    def build(self) -> DependencyReport:
        """Scan all .py files, parse imports via AST, and build the dependency graph."""
        logger.info("Building static dependency graph from %s", self._root)
        start = time.monotonic()

        self._edges = []
        self._graph = defaultdict(set)
        self._all_modules = set()
        self._external_deps = set()

        for py_file in self._iter_python_files():
            module_name = self._path_to_module(py_file)
            if module_name is None:
                continue

            self._all_modules.add(module_name)
            edges = self._scan_file(py_file, module_name)
            self._edges.extend(edges)

            for edge in edges:
                if not edge.is_type_checking:
                    self._graph[edge.source_module].add(edge.target_module)

        cycles = self.find_cycles()

        elapsed = (time.monotonic() - start) * 1000
        report = DependencyReport(
            edges=self._edges,
            cycles=cycles,
            external_deps=self._external_deps.copy(),
            module_count=len(self._all_modules),
            edge_count=len(self._edges),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        self._built = True
        logger.info(
            "Static graph built: %d modules, %d edges, %d cycles (%.1fms)",
            report.module_count, report.edge_count, len(cycles), elapsed,
        )
        return report

    def get_graph(self) -> dict[str, list[str]]:
        """Return adjacency list of module dependencies (runtime imports only)."""
        return {k: sorted(v) for k, v in self._graph.items()}

    def find_cycles(self) -> list[list[str]]:
        """Detect circular dependency chains using iterative DFS with back-edge detection."""
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []
        seen_cycles: set[tuple[str, ...]] = set()

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in sorted(self._graph.get(node, set())):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    normalized = tuple(sorted(cycle[:-1]))
                    if normalized not in seen_cycles:
                        seen_cycles.add(normalized)
                        cycles.append(cycle)

            path.pop()
            rec_stack.discard(node)

        for node in sorted(self._all_modules):
            if node not in visited:
                dfs(node)

        return cycles

    def get_external_dependencies(self) -> set[str]:
        """Return all external (non-ambient-os) import targets."""
        return self._external_deps.copy()

    def get_all_modules(self) -> set[str]:
        """Return set of all discovered internal module paths."""
        return self._all_modules.copy()

    def get_edges(self) -> list[ImportEdge]:
        """Return all discovered import edges."""
        return list(self._edges)

    # ── Internal Methods ──────────────────────────────────────────────────

    def _scan_file(self, path: Path, source_module: str) -> list[ImportEdge]:
        """Parse one file's imports via AST."""
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (SyntaxError, UnicodeDecodeError, OSError) as exc:
            logger.warning("Failed to parse %s: %s", path, exc)
            return []

        type_checking_ranges = self._find_type_checking_ranges(tree)
        edges: list[ImportEdge] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = self._resolve_module(alias.name)
                    in_tc = self._is_in_range(node.lineno, type_checking_ranges)
                    if target is None:
                        self._external_deps.add(alias.name.split(".")[0])
                    else:
                        edges.append(ImportEdge(
                            source_module=source_module,
                            target_module=target,
                            import_type="import",
                            line_number=node.lineno,
                            is_type_checking=in_tc,
                        ))

            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                if node.level > 0:
                    module_name = self._resolve_relative(
                        source_module, module_name, node.level
                    )

                target = self._resolve_module(module_name)
                in_tc = self._is_in_range(node.lineno, type_checking_ranges)
                if target is None:
                    if module_name:
                        self._external_deps.add(module_name.split(".")[0])
                else:
                    edges.append(ImportEdge(
                        source_module=source_module,
                        target_module=target,
                        import_type="from",
                        line_number=node.lineno,
                        is_type_checking=in_tc,
                    ))

        return edges

    def _resolve_module(self, module_name: str) -> str | None:
        """Resolve import to an internal module path, or None if external."""
        if not module_name:
            return None

        top_level = module_name.split(".")[0]
        if top_level not in KNOWN_TOP_LEVEL_PACKAGES:
            return None

        return module_name

    def _resolve_relative(self, source_module: str, module_name: str, level: int) -> str:
        """Resolve a relative import to its absolute module path."""
        parts = source_module.split(".")
        if level > len(parts):
            return module_name

        base = ".".join(parts[:-level]) if level > 0 else source_module
        if module_name:
            return f"{base}.{module_name}" if base else module_name
        return base

    def _find_type_checking_ranges(self, tree: ast.Module) -> list[tuple[int, int]]:
        """Find line ranges of `if TYPE_CHECKING:` blocks."""
        ranges: list[tuple[int, int]] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.If):
                continue

            test = node.test
            is_type_checking = False

            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                is_type_checking = True
            elif isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
                is_type_checking = True

            if is_type_checking:
                start_line = node.lineno
                end_line = max(
                    (getattr(child, 'end_lineno', start_line) or start_line)
                    for child in ast.walk(node)
                )
                ranges.append((start_line, end_line))

        return ranges

    @staticmethod
    def _is_in_range(line: int, ranges: list[tuple[int, int]]) -> bool:
        """Check if a line number falls within any of the given ranges."""
        return any(start <= line <= end for start, end in ranges)

    def _path_to_module(self, path: Path) -> str | None:
        """Convert a filesystem path to a dotted module name."""
        try:
            rel = path.relative_to(self._root)
        except ValueError:
            return None

        parts = list(rel.parts)
        if not parts:
            return None

        if parts[0] not in KNOWN_TOP_LEVEL_PACKAGES:
            return None

        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        elif parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]
        else:
            return None

        return ".".join(parts)

    def _iter_python_files(self) -> list[Path]:
        """Iterate all .py files in the root, skipping excluded directories."""
        results: list[Path] = []

        for py_file in self._root.rglob("*.py"):
            parts = py_file.relative_to(self._root).parts
            if any(part in SKIP_DIRS for part in parts):
                continue
            results.append(py_file)

        return sorted(results)
