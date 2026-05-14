"""
Architecture Drift Detection — Observability layer for structural health.

Monitors the system's architecture for inconsistencies, dependency drift,
and integration integrity issues. Generates remediation proposals (not
auto-fixes) and provides multi-dimensional health scoring.

Components:
  consistency_scanner.py  — Detects orphaned modules, broken imports, missing exports
  dependency_drift.py     — Compares dependencies against baseline, detects cycles
  integration_checker.py  — Verifies all 16 integration bus connections
  drift_detector.py       — Unified orchestrator combining all analyzers
  health_scorer.py        — Multi-dimensional health scoring (A-F grade)
"""

from observability.drift_detection.consistency_scanner import (
    ConsistencyScanner,
    ConsistencyScanResult,
    ConsistencyIssue,
    IssueSeverity,
)
from observability.drift_detection.dependency_drift import (
    DependencyDriftAnalyzer,
    DriftReport,
)
from observability.drift_detection.integration_checker import (
    IntegrationIntegrityChecker,
    IntegrityReport,
    ConnectionStatus,
)
from observability.drift_detection.drift_detector import (
    DriftDetector,
    UnifiedDriftReport,
    RemediationProposal,
    RemediationSeverity,
)
from observability.drift_detection.health_scorer import (
    ArchitectureHealthScorer,
    HealthScore,
    HealthDimension,
)

__all__ = [
    "ConsistencyScanner",
    "ConsistencyScanResult",
    "ConsistencyIssue",
    "IssueSeverity",
    "DependencyDriftAnalyzer",
    "DriftReport",
    "IntegrationIntegrityChecker",
    "IntegrityReport",
    "ConnectionStatus",
    "DriftDetector",
    "UnifiedDriftReport",
    "RemediationProposal",
    "RemediationSeverity",
    "ArchitectureHealthScorer",
    "HealthScore",
    "HealthDimension",
]
