"""
Graph Truth Layer — The authoritative source of architecture verification.

This subsystem continuously verifies the system's own architecture through
static analysis, runtime verification, bus consistency checking, orphan
detection, and coupling analysis. The graph truth layer IS the authority
on architectural correctness — the IntegrationBus is not.

Components:
  static_dependency_graph.py     — AST-based import dependency graph builder
  runtime_dependency_verifier.py — Verifies runtime imports match static graph
  bus_consistency_checker.py     — Verifies IntegrationBus connection health
  orphan_module_detector.py      — Finds modules unreachable from kernel boot
  coupling_analyzer.py           — Detects cross-layer coupling violations
"""

from architecture.graph_truth_layer.static_dependency_graph import (
    StaticDependencyGraph,
    ImportEdge,
    DependencyReport,
)
from architecture.graph_truth_layer.runtime_dependency_verifier import (
    RuntimeDependencyVerifier,
    VerificationReport,
)
from architecture.graph_truth_layer.bus_consistency_checker import (
    BusConsistencyChecker,
    ConnectionStatus,
    MonkeyPatchStatus,
    ListenerStatus,
    BusConsistencyReport,
)
from architecture.graph_truth_layer.orphan_module_detector import (
    OrphanModuleDetector,
    OrphanModule,
    OrphanReport,
)
from architecture.graph_truth_layer.coupling_analyzer import (
    CouplingAnalyzer,
    CouplingViolation,
    DuplicateConstant,
    CouplingReport,
)

__all__ = [
    "StaticDependencyGraph",
    "ImportEdge",
    "DependencyReport",
    "RuntimeDependencyVerifier",
    "VerificationReport",
    "BusConsistencyChecker",
    "ConnectionStatus",
    "MonkeyPatchStatus",
    "ListenerStatus",
    "BusConsistencyReport",
    "OrphanModuleDetector",
    "OrphanModule",
    "OrphanReport",
    "CouplingAnalyzer",
    "CouplingViolation",
    "DuplicateConstant",
    "CouplingReport",
]
