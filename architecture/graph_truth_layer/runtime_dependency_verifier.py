"""
Runtime Dependency Verifier — Verifies actual runtime imports match the static graph.

At boot time (or on demand), compares what sys.modules has loaded against
the static dependency graph to find undeclared runtime imports and unused
declared dependencies.
"""

from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from architecture.graph_truth_layer.static_dependency_graph import StaticDependencyGraph

logger = logging.getLogger("architecture.graph_truth_layer.runtime_dependency_verifier")

KNOWN_TOP_LEVEL_PACKAGES = {
    "kernel", "agents", "governance", "memory", "context",
    "runtime", "somatic", "observability", "identity",
    "architecture", "scripts", "tools",
}


@dataclass
class VerificationReport:
    """Result of comparing static graph with runtime sys.modules."""
    undeclared: list[str] = field(default_factory=list)
    unused: list[str] = field(default_factory=list)
    total_declared: int = 0
    total_loaded: int = 0
    is_consistent: bool = True
    verified_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "undeclared_count": len(self.undeclared),
            "undeclared": self.undeclared[:50],
            "unused_count": len(self.unused),
            "unused": self.unused[:50],
            "total_declared": self.total_declared,
            "total_loaded": self.total_loaded,
            "is_consistent": self.is_consistent,
            "verified_at": self.verified_at,
        }


class RuntimeDependencyVerifier:
    """
    Verifies that actual runtime imports match the static dependency graph.

    Detects:
      - Undeclared imports: modules loaded at runtime but absent from static graph
      - Unused declarations: modules in the static graph that were never loaded
    """

    def __init__(self, static_graph: "StaticDependencyGraph"):
        self._static_graph = static_graph

    def verify(self) -> VerificationReport:
        """Compare static graph with sys.modules."""
        logger.info("Verifying runtime dependencies against static graph...")
        start = time.monotonic()

        loaded_modules = self._get_loaded_modules()
        declared_modules = self._static_graph.get_all_modules()

        undeclared = self._find_undeclared_imports(declared_modules, loaded_modules)
        unused = self._find_unused_declarations(declared_modules, loaded_modules)

        is_consistent = len(undeclared) == 0

        elapsed = (time.monotonic() - start) * 1000
        report = VerificationReport(
            undeclared=sorted(undeclared),
            unused=sorted(unused),
            total_declared=len(declared_modules),
            total_loaded=len(loaded_modules),
            is_consistent=is_consistent,
            verified_at=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            "Runtime verification: declared=%d, loaded=%d, undeclared=%d, "
            "unused=%d, consistent=%s (%.1fms)",
            report.total_declared, report.total_loaded,
            len(undeclared), len(unused), is_consistent, elapsed,
        )
        return report

    def _get_loaded_modules(self) -> set[str]:
        """Filter sys.modules for ambient-os internal modules."""
        loaded: set[str] = set()

        for module_name in sys.modules:
            top_level = module_name.split(".")[0]
            if top_level in KNOWN_TOP_LEVEL_PACKAGES:
                loaded.add(module_name)

        return loaded

    def _find_undeclared_imports(
        self, declared: set[str], loaded: set[str]
    ) -> list[str]:
        """Find modules loaded at runtime but not in the static graph."""
        undeclared: list[str] = []

        for module_name in loaded:
            if module_name in declared:
                continue

            # A loaded module might be a parent package of a declared module
            is_parent_of_declared = any(
                d.startswith(module_name + ".") for d in declared
            )
            if is_parent_of_declared:
                continue

            # A loaded module might be a child that resolves to a declared parent
            is_child_of_declared = any(
                module_name.startswith(d + ".") for d in declared
            )
            if is_child_of_declared:
                continue

            undeclared.append(module_name)

        return undeclared

    def _find_unused_declarations(
        self, declared: set[str], loaded: set[str]
    ) -> list[str]:
        """Find modules in the static graph that were never loaded at runtime."""
        unused: list[str] = []

        for module_name in declared:
            if module_name in loaded:
                continue

            is_loaded_as_parent = any(
                l.startswith(module_name + ".") for l in loaded
            )
            if is_loaded_as_parent:
                continue

            is_loaded_via_parent = any(
                module_name.startswith(l + ".") for l in loaded
            )
            if is_loaded_via_parent:
                continue

            unused.append(module_name)

        return unused
