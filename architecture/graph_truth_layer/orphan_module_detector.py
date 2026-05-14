"""
Orphan Module Detector — Finds modules not reachable from kernel boot path.

Uses the static dependency graph to BFS/DFS from known entry points and
identifies modules that cannot be reached through any import chain from
the kernel boot sequence.
"""

from __future__ import annotations

import ast
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from architecture.graph_truth_layer.static_dependency_graph import StaticDependencyGraph

logger = logging.getLogger("architecture.graph_truth_layer.orphan_module_detector")

ENTRY_POINTS = [
    "kernel",
    "kernel.__init__",
    "kernel.bootstrap",
    "kernel.integration_bus",
]

SKIP_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules", ".mypy_cache", ".pytest_cache"}

KNOWN_TOP_LEVEL_PACKAGES = {
    "kernel", "agents", "governance", "memory", "context",
    "runtime", "somatic", "observability", "identity",
    "architecture", "scripts", "tools",
}


@dataclass
class OrphanModule:
    """A module not reachable from any entry point."""
    module_path: str
    reason: str
    has_classes: bool
    line_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_path": self.module_path,
            "reason": self.reason,
            "has_classes": self.has_classes,
            "line_count": self.line_count,
        }


@dataclass
class OrphanReport:
    """Result of orphan module detection."""
    orphans: list[OrphanModule] = field(default_factory=list)
    total_modules: int = 0
    reachable_modules: int = 0
    orphan_rate: float = 0.0
    detected_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "orphan_count": len(self.orphans),
            "orphans": [o.to_dict() for o in self.orphans],
            "total_modules": self.total_modules,
            "reachable_modules": self.reachable_modules,
            "orphan_rate": round(self.orphan_rate, 4),
            "detected_at": self.detected_at,
        }


class OrphanModuleDetector:
    """
    Finds modules not reachable from the kernel boot path by traversing
    the static dependency graph from known entry points.
    """

    def __init__(self, root_dir: Path, static_graph: "StaticDependencyGraph"):
        self._root = root_dir.resolve()
        self._static_graph = static_graph

    def detect(self) -> OrphanReport:
        """Find unreachable modules from all entry points."""
        logger.info("Detecting orphan modules...")
        start = time.monotonic()

        all_modules = self._get_all_modules()
        graph = self._static_graph.get_graph()

        reachable: set[str] = set()
        for entry_point in ENTRY_POINTS:
            reachable.update(self._get_reachable_from(entry_point, graph))

        orphan_set = all_modules - reachable
        orphans = self._classify_orphans(orphan_set)

        total = len(all_modules)
        reachable_count = len(reachable & all_modules)
        orphan_rate = len(orphans) / max(total, 1)

        elapsed = (time.monotonic() - start) * 1000
        report = OrphanReport(
            orphans=orphans,
            total_modules=total,
            reachable_modules=reachable_count,
            orphan_rate=orphan_rate,
            detected_at=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            "Orphan detection: %d/%d modules unreachable (%.1f%%) (%.1fms)",
            len(orphans), total, orphan_rate * 100, elapsed,
        )
        return report

    def _get_all_modules(self) -> set[str]:
        """Scan filesystem for all .py modules in known packages."""
        modules: set[str] = set()

        for py_file in self._root.rglob("*.py"):
            parts = py_file.relative_to(self._root).parts
            if any(part in SKIP_DIRS for part in parts):
                continue
            if not parts or parts[0] not in KNOWN_TOP_LEVEL_PACKAGES:
                continue

            module_parts = list(parts)
            if module_parts[-1] == "__init__.py":
                module_parts = module_parts[:-1]
            elif module_parts[-1].endswith(".py"):
                module_parts[-1] = module_parts[-1][:-3]
            else:
                continue

            modules.add(".".join(module_parts))

        return modules

    def _get_reachable_from(self, entry_point: str, graph: dict[str, list[str]]) -> set[str]:
        """BFS from entry point through the dependency graph."""
        reachable: set[str] = set()
        queue: deque[str] = deque()

        queue.append(entry_point)
        reachable.add(entry_point)

        while queue:
            current = queue.popleft()

            for neighbor in graph.get(current, []):
                if neighbor not in reachable:
                    reachable.add(neighbor)
                    queue.append(neighbor)

            # Also traverse parent packages (kernel.integration_bus → kernel reachable)
            parts = current.split(".")
            for i in range(1, len(parts)):
                parent = ".".join(parts[:i])
                if parent not in reachable:
                    reachable.add(parent)
                    queue.append(parent)

        return reachable

    def _classify_orphans(self, orphans: set[str]) -> list[OrphanModule]:
        """Classify why each orphan is unreachable."""
        results: list[OrphanModule] = []

        for module_path in sorted(orphans):
            file_path = self._module_to_path(module_path)
            if file_path is None or not file_path.exists():
                continue

            has_classes = False
            line_count = 0
            reason = "no_import_chain"

            try:
                source = file_path.read_text(encoding="utf-8")
                line_count = source.count("\n") + 1
                tree = ast.parse(source, filename=str(file_path))

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        has_classes = True
                        break

                reason = self._determine_reason(module_path, has_classes, line_count)
            except (SyntaxError, UnicodeDecodeError, OSError):
                reason = "parse_error"

            results.append(OrphanModule(
                module_path=module_path,
                reason=reason,
                has_classes=has_classes,
                line_count=line_count,
            ))

        return results

    def _determine_reason(self, module_path: str, has_classes: bool, line_count: int) -> str:
        """Determine why a module is orphaned."""
        if line_count <= 5:
            return "stub_or_empty"

        parts = module_path.split(".")
        if any(p.startswith("test") or p == "tests" for p in parts):
            return "test_module"

        if parts[-1] in ("__main__", "cli", "main"):
            return "standalone_entry"

        if not has_classes and line_count < 20:
            return "utility_snippet"

        return "no_import_chain"

    def _module_to_path(self, module_path: str) -> Path | None:
        """Convert a dotted module path to a filesystem path."""
        parts = module_path.split(".")
        candidate = self._root / "/".join(parts)

        # Try as package
        init_path = candidate / "__init__.py"
        if init_path.exists():
            return init_path

        # Try as module file
        file_path = candidate.with_suffix(".py")
        if file_path.exists():
            return file_path

        return None
