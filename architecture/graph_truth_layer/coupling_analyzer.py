"""
Coupling Analyzer — Detects cross-layer coupling violations and duplicate constants.

Assigns each module to an architectural layer and identifies imports that
violate the layering constraints (lower layers importing from higher layers).
Also detects constants duplicated across multiple modules.
"""

from __future__ import annotations

import ast
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from architecture.graph_truth_layer.static_dependency_graph import StaticDependencyGraph

logger = logging.getLogger("architecture.graph_truth_layer.coupling_analyzer")

LAYER_ASSIGNMENTS: dict[int, list[str]] = {
    0: ["scripts"],
    1: ["memory", "somatic.signal_bus"],
    2: ["context", "governance", "agents", "runtime", "somatic"],
    3: ["kernel"],
    4: ["observability", "identity"],
}

# Constants known to be duplicated from Phase 0 audit
KNOWN_DUPLICATE_CONSTANTS = [
    "AMBIENT_ROOT",
    "AGENTS_STATE_DIR",
    "LAYERS",
    "LAYER_WEIGHT",
    "STOP_WORDS",
]

SKIP_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules", ".mypy_cache", ".pytest_cache"}

KNOWN_TOP_LEVEL_PACKAGES = {
    "kernel", "agents", "governance", "memory", "context",
    "runtime", "somatic", "observability", "identity",
    "architecture", "scripts", "tools",
}


@dataclass
class CouplingViolation:
    """A detected layer boundary violation."""
    source_module: str
    source_layer: int
    target_module: str
    target_layer: int
    import_line: int
    severity: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_module": self.source_module,
            "source_layer": self.source_layer,
            "target_module": self.target_module,
            "target_layer": self.target_layer,
            "import_line": self.import_line,
            "severity": self.severity,
            "direction": f"L{self.source_layer} → L{self.target_layer}",
        }


@dataclass
class DuplicateConstant:
    """A constant defined in multiple modules."""
    name: str
    locations: list[str] = field(default_factory=list)
    values_match: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "locations": self.locations,
            "location_count": len(self.locations),
            "values_match": self.values_match,
        }


@dataclass
class CouplingReport:
    """Full coupling analysis result."""
    violations: list[CouplingViolation] = field(default_factory=list)
    duplicates: list[DuplicateConstant] = field(default_factory=list)
    coupling_score: float = 0.0
    layer_summary: dict[int, int] = field(default_factory=dict)
    analyzed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "violation_count": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
            "duplicate_count": len(self.duplicates),
            "duplicates": [d.to_dict() for d in self.duplicates],
            "coupling_score": round(self.coupling_score, 4),
            "layer_summary": self.layer_summary,
            "analyzed_at": self.analyzed_at,
        }


class CouplingAnalyzer:
    """
    Analyzes cross-layer coupling violations in the architecture.

    Layer constraints (lower number = lower layer):
      Layer 0 (Foundation): scripts — stdlib only
      Layer 1 (Core): memory, somatic.signal_bus — foundational data
      Layer 2 (Services): context, governance, agents, runtime, somatic
      Layer 3 (Integration): kernel — wires everything
      Layer 4 (Observability): observability, identity — observe but don't modify

    Violation = Layer N importing from Layer N+1 or higher
    """

    def __init__(self, static_graph: "StaticDependencyGraph"):
        self._static_graph = static_graph
        self._layer_cache: dict[str, int] = {}

    def analyze(self) -> CouplingReport:
        """Run full coupling analysis."""
        logger.info("Running coupling analysis...")
        start = time.monotonic()

        self._layer_cache = self._assign_layers()
        violations = self._find_violations()
        duplicates = self._find_duplicate_constants()
        coupling_score = self._compute_coupling_score(violations)
        layer_summary = self._build_layer_summary()

        elapsed = (time.monotonic() - start) * 1000
        report = CouplingReport(
            violations=violations,
            duplicates=duplicates,
            coupling_score=coupling_score,
            layer_summary=layer_summary,
            analyzed_at=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            "Coupling analysis: %d violations, %d duplicates, "
            "score=%.3f (%.1fms)",
            len(violations), len(duplicates), coupling_score, elapsed,
        )
        return report

    def _assign_layers(self) -> dict[str, int]:
        """Assign each module to an architectural layer."""
        assignments: dict[str, int] = {}
        all_modules = self._static_graph.get_all_modules()

        for module in all_modules:
            layer = self._get_layer_for_module(module)
            assignments[module] = layer

        return assignments

    def _get_layer_for_module(self, module: str) -> int:
        """Determine which layer a module belongs to."""
        # Check from most specific to least specific
        for layer_num, prefixes in sorted(LAYER_ASSIGNMENTS.items()):
            for prefix in prefixes:
                if module == prefix or module.startswith(prefix + "."):
                    return layer_num

        # Default: if it's in a known package but not explicitly assigned
        top_level = module.split(".")[0]
        if top_level == "architecture":
            return 4
        if top_level in KNOWN_TOP_LEVEL_PACKAGES:
            # Fall back to heuristic based on top-level
            fallback_map = {
                "scripts": 0,
                "memory": 1,
                "somatic": 2,
                "context": 2,
                "governance": 2,
                "agents": 2,
                "runtime": 2,
                "kernel": 3,
                "observability": 4,
                "identity": 4,
                "tools": 0,
                "architecture": 4,
            }
            return fallback_map.get(top_level, 2)

        return -1

    def _find_violations(self) -> list[CouplingViolation]:
        """Find imports that cross layer boundaries upward."""
        violations: list[CouplingViolation] = []
        edges = self._static_graph.get_edges()

        for edge in edges:
            if edge.is_type_checking:
                continue

            source_layer = self._layer_cache.get(edge.source_module, -1)
            target_layer = self._layer_cache.get(edge.target_module, -1)

            if source_layer < 0 or target_layer < 0:
                continue

            # Violation: lower layer imports from higher layer
            if source_layer < target_layer:
                layer_diff = target_layer - source_layer
                severity = "critical" if layer_diff >= 2 else "warning"

                violations.append(CouplingViolation(
                    source_module=edge.source_module,
                    source_layer=source_layer,
                    target_module=edge.target_module,
                    target_layer=target_layer,
                    import_line=edge.line_number,
                    severity=severity,
                ))

        return violations

    def _find_duplicate_constants(self) -> list[DuplicateConstant]:
        """Detect same constant defined in multiple modules."""
        results: list[DuplicateConstant] = []
        root = self._get_root()

        for const_name in KNOWN_DUPLICATE_CONSTANTS:
            locations: list[str] = []
            values: list[str] = []

            for py_file in root.rglob("*.py"):
                parts = py_file.relative_to(root).parts
                if any(part in SKIP_DIRS for part in parts):
                    continue
                if not parts or parts[0] not in KNOWN_TOP_LEVEL_PACKAGES:
                    continue

                try:
                    source = py_file.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue

                # Quick text check before expensive AST parse
                if const_name not in source:
                    continue

                try:
                    tree = ast.parse(source, filename=str(py_file))
                except SyntaxError:
                    continue

                for node in ast.walk(tree):
                    if not isinstance(node, ast.Assign):
                        continue

                    for target in node.targets:
                        target_name = None
                        if isinstance(target, ast.Name):
                            target_name = target.id
                        elif isinstance(target, ast.Attribute):
                            target_name = target.attr

                        if target_name == const_name:
                            rel_path = str(py_file.relative_to(root))
                            locations.append(f"{rel_path}:{node.lineno}")
                            try:
                                values.append(ast.unparse(node.value))
                            except Exception:
                                values.append("?")

            if len(locations) >= 2:
                unique_values = set(values)
                results.append(DuplicateConstant(
                    name=const_name,
                    locations=locations,
                    values_match=len(unique_values) <= 1,
                ))

        return results

    def _compute_coupling_score(self, violations: list[CouplingViolation]) -> float:
        """Compute coupling score from 0.0 (decoupled) to 1.0 (fully coupled)."""
        if not violations:
            return 0.0

        all_modules = self._static_graph.get_all_modules()
        total_edges = len(self._static_graph.get_edges())

        if total_edges == 0:
            return 0.0

        weighted_violations = sum(
            2.0 if v.severity == "critical" else 1.0
            for v in violations
        )

        # Normalized by total edge count
        raw_score = weighted_violations / max(total_edges, 1)
        return min(1.0, raw_score)

    def _build_layer_summary(self) -> dict[int, int]:
        """Count modules per layer."""
        summary: dict[int, int] = {}
        for layer in self._layer_cache.values():
            summary[layer] = summary.get(layer, 0) + 1
        return dict(sorted(summary.items()))

    def _get_root(self) -> Path:
        """Get the root directory from the static graph."""
        return self._static_graph._root
