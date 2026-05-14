"""
Drift Detector — Unified architecture drift detection combining all analyzers.

Orchestrates ConsistencyScanner, DependencyDriftAnalyzer, and
IntegrationIntegrityChecker into a single detection pass. Generates
remediation proposals (NOT auto-fixes) and formatted review packets.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from identity.cognitive_self_model.self_model import CognitiveSelfModel
    from kernel.integration_bus import IntegrationBus

from observability.drift_detection.consistency_scanner import (
    ConsistencyScanner,
    ConsistencyScanResult,
)
from observability.drift_detection.dependency_drift import (
    DependencyDriftAnalyzer,
    DriftReport as DepDriftReport,
)
from observability.drift_detection.integration_checker import (
    IntegrationIntegrityChecker,
    IntegrityReport,
)

logger = logging.getLogger("observability.drift_detection.drift_detector")

AMBIENT_ROOT = Path(__file__).resolve().parent.parent.parent


class RemediationSeverity(str, Enum):
    """Severity for remediation proposals."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RemediationProposal:
    """A proposed fix for a detected drift issue — NOT an auto-fix."""
    description: str
    severity: RemediationSeverity
    proposed_fix: str
    risk_score: float = 0.0
    reversibility: str = "fully_reversible"
    category: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "severity": self.severity.value,
            "proposed_fix": self.proposed_fix,
            "risk_score": round(self.risk_score, 1),
            "reversibility": self.reversibility,
            "category": self.category,
        }


@dataclass
class UnifiedDriftReport:
    """Combined drift report from all analyzers."""
    consistency: ConsistencyScanResult | None = None
    dependency_drift: DepDriftReport | None = None
    integration: IntegrityReport | None = None
    remediation_proposals: list[RemediationProposal] = field(default_factory=list)
    overall_risk_score: float = 0.0
    detection_timestamp: str = ""
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "consistency": self.consistency.to_dict() if self.consistency else None,
            "dependency_drift": self.dependency_drift.to_dict() if self.dependency_drift else None,
            "integration": self.integration.to_dict() if self.integration else None,
            "remediation_proposals": [p.to_dict() for p in self.remediation_proposals],
            "proposal_count": len(self.remediation_proposals),
            "overall_risk_score": round(self.overall_risk_score, 1),
            "detection_timestamp": self.detection_timestamp,
            "elapsed_ms": round(self.elapsed_ms, 1),
        }


class DriftDetector:
    """
    Unified drift detection combining all analyzers.

    Runs consistency scanning, dependency drift analysis, and integration
    integrity checking in one pass, then generates remediation proposals.

    IMPORTANT: This detector does NOT auto-repair anything.
    It only generates proposals for human review.
    """

    def __init__(self, root: Path | None = None):
        self._root = root or AMBIENT_ROOT
        self._consistency_scanner = ConsistencyScanner(root=self._root)
        self._dep_drift_analyzer = DependencyDriftAnalyzer(root=self._root)
        self._integration_checker = IntegrationIntegrityChecker()

    def detect(
        self,
        self_model: "CognitiveSelfModel",
        bus: "IntegrationBus | None" = None,
    ) -> UnifiedDriftReport:
        """Run all analyzers and return a combined drift report."""
        logger.info("Running unified drift detection...")
        start = time.monotonic()

        consistency_result = self._consistency_scanner.scan(self_model)

        from identity.cognitive_self_model.dependency_graph import DependencyGraph
        dep_graph = DependencyGraph()
        from identity.cognitive_self_model.architecture_graph import ArchitectureGraph
        arch = ArchitectureGraph(root=self._root)
        arch.build()
        dep_graph.build_from_architecture(arch)
        dep_drift_result = self._dep_drift_analyzer.analyze(dep_graph)

        integration_result = self._integration_checker.check(bus)

        elapsed = (time.monotonic() - start) * 1000

        overall_risk = self._compute_overall_risk(
            consistency_result, dep_drift_result, integration_result
        )

        report = UnifiedDriftReport(
            consistency=consistency_result,
            dependency_drift=dep_drift_result,
            integration=integration_result,
            overall_risk_score=overall_risk,
            detection_timestamp=datetime.now(timezone.utc).isoformat(),
            elapsed_ms=elapsed,
        )

        report.remediation_proposals = self.generate_remediation_proposals(report)

        logger.info(
            "Drift detection complete: risk=%.1f, proposals=%d (%.1fms)",
            overall_risk, len(report.remediation_proposals), elapsed,
        )
        return report

    def generate_remediation_proposals(
        self, drift_report: UnifiedDriftReport
    ) -> list[RemediationProposal]:
        """Generate remediation proposals for detected issues."""
        proposals: list[RemediationProposal] = []

        if drift_report.consistency:
            proposals.extend(
                self._proposals_from_consistency(drift_report.consistency)
            )

        if drift_report.dependency_drift:
            proposals.extend(
                self._proposals_from_dep_drift(drift_report.dependency_drift)
            )

        if drift_report.integration:
            proposals.extend(
                self._proposals_from_integration(drift_report.integration)
            )

        proposals.sort(key=lambda p: (
            {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(p.severity.value, 4),
            -p.risk_score,
        ))

        return proposals

    def create_review_packet(self, drift_report: UnifiedDriftReport) -> str:
        """Generate a formatted review document from the drift report."""
        lines: list[str] = []
        lines.append("=" * 70)
        lines.append("ARCHITECTURE DRIFT DETECTION — REVIEW PACKET")
        lines.append("=" * 70)
        lines.append(f"Generated: {drift_report.detection_timestamp}")
        lines.append(f"Overall Risk Score: {drift_report.overall_risk_score:.1f}/100")
        lines.append("")

        lines.append("─" * 50)
        lines.append("1. CONSISTENCY SCAN")
        lines.append("─" * 50)
        if drift_report.consistency:
            c = drift_report.consistency
            lines.append(f"  Score: {c.overall_score:.1f}/100")
            lines.append(f"  Issues: {len(c.issues)}")
            for issue in c.issues[:10]:
                lines.append(f"    [{issue.severity.value}] {issue.description}")
                if issue.suggestion:
                    lines.append(f"         → {issue.suggestion}")
        lines.append("")

        lines.append("─" * 50)
        lines.append("2. DEPENDENCY DRIFT")
        lines.append("─" * 50)
        if drift_report.dependency_drift:
            d = drift_report.dependency_drift
            lines.append(f"  Risk Score: {d.risk_score:.1f}/100")
            lines.append(f"  New Dependencies: {len(d.new_deps)}")
            lines.append(f"  Removed Dependencies: {len(d.removed_deps)}")
            lines.append(f"  Circular Dependencies: {len(d.circular_deps)}")
            lines.append(f"  Dead Dependencies: {len(d.dead_deps)}")
            for dep in d.new_deps[:5]:
                lines.append(f"    NEW: {dep['from']} → {dep['to']}")
            for cycle in d.circular_deps[:3]:
                lines.append(f"    CYCLE: {' → '.join(cycle)}")
        lines.append("")

        lines.append("─" * 50)
        lines.append("3. INTEGRATION INTEGRITY")
        lines.append("─" * 50)
        if drift_report.integration:
            i = drift_report.integration
            lines.append(f"  Health Score: {i.health_score:.1f}/100")
            lines.append(f"  Valid: {len(i.valid_connections)}/{i.total_expected}")
            lines.append(f"  Broken: {len(i.broken_connections)}")
            for b in i.broken_connections[:5]:
                lines.append(f"    BROKEN: {b.name} — {b.warning}")
            for w in i.warnings[:5]:
                lines.append(f"    WARNING: {w}")
        lines.append("")

        lines.append("─" * 50)
        lines.append("4. REMEDIATION PROPOSALS")
        lines.append("─" * 50)
        for idx, prop in enumerate(drift_report.remediation_proposals[:15], 1):
            lines.append(
                f"  {idx}. [{prop.severity.value}] {prop.description}"
            )
            lines.append(f"     Fix: {prop.proposed_fix}")
            lines.append(f"     Risk: {prop.risk_score:.0f} | {prop.reversibility}")
            lines.append("")

        lines.append("=" * 70)
        lines.append("END OF REVIEW PACKET")
        lines.append("=" * 70)

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Serializable representation of the detector configuration."""
        return {
            "root": str(self._root),
            "analyzers": [
                "ConsistencyScanner",
                "DependencyDriftAnalyzer",
                "IntegrationIntegrityChecker",
            ],
            "expected_connections": EXPECTED_CONNECTIONS,
        }

    # ── Internal: Proposal Generation ────────────────────────────────────

    def _proposals_from_consistency(
        self, result: ConsistencyScanResult
    ) -> list[RemediationProposal]:
        """Generate proposals from consistency scan issues."""
        proposals: list[RemediationProposal] = []

        severity_map = {
            "INFO": RemediationSeverity.LOW,
            "LOW": RemediationSeverity.LOW,
            "MEDIUM": RemediationSeverity.MEDIUM,
            "HIGH": RemediationSeverity.HIGH,
            "CRITICAL": RemediationSeverity.CRITICAL,
        }

        for issue in result.issues:
            proposals.append(RemediationProposal(
                description=issue.description,
                severity=severity_map.get(issue.severity.value, RemediationSeverity.MEDIUM),
                proposed_fix=issue.suggestion or "Review and address the inconsistency",
                risk_score=self._severity_to_risk(issue.severity.value),
                reversibility="fully_reversible",
                category=issue.category,
            ))

        return proposals

    def _proposals_from_dep_drift(
        self, result: DepDriftReport
    ) -> list[RemediationProposal]:
        """Generate proposals from dependency drift analysis."""
        proposals: list[RemediationProposal] = []

        for dep in result.new_deps:
            proposals.append(RemediationProposal(
                description=f"Unexpected dependency: {dep['from']} → {dep['to']}",
                severity=RemediationSeverity.MEDIUM,
                proposed_fix=(
                    f"Review if dependency from {dep['from']} to {dep['to']} "
                    f"is intentional. If so, update the baseline."
                ),
                risk_score=30.0,
                reversibility="fully_reversible",
                category="new_dependency",
            ))

        for cycle in result.circular_deps:
            proposals.append(RemediationProposal(
                description=f"Circular dependency detected: {' → '.join(cycle)}",
                severity=RemediationSeverity.HIGH,
                proposed_fix=(
                    "Break the cycle by introducing an interface/protocol layer "
                    "or restructuring imports to use late binding."
                ),
                risk_score=60.0,
                reversibility="requires_refactoring",
                category="circular_dependency",
            ))

        for dead in result.dead_deps:
            proposals.append(RemediationProposal(
                description=f"Dead dependency target: {dead.get('target', 'unknown')}",
                severity=RemediationSeverity.LOW,
                proposed_fix="Remove references to the non-existent target module",
                risk_score=15.0,
                reversibility="fully_reversible",
                category="dead_dependency",
            ))

        return proposals

    def _proposals_from_integration(
        self, result: IntegrityReport
    ) -> list[RemediationProposal]:
        """Generate proposals from integration integrity issues."""
        proposals: list[RemediationProposal] = []

        for broken in result.broken_connections:
            proposals.append(RemediationProposal(
                description=f"Broken bus connection: {broken.name}",
                severity=RemediationSeverity.HIGH,
                proposed_fix=(
                    f"Implement or fix _wire_{broken.name}() method "
                    f"in IntegrationBus. {broken.warning}"
                ),
                risk_score=50.0,
                reversibility="fully_reversible",
                category="broken_connection",
            ))

        for warning in result.warnings:
            proposals.append(RemediationProposal(
                description=f"Integration warning: {warning}",
                severity=RemediationSeverity.LOW,
                proposed_fix="Review and address the warning condition",
                risk_score=10.0,
                reversibility="fully_reversible",
                category="integration_warning",
            ))

        return proposals

    # ── Internal Helpers ─────────────────────────────────────────────────

    def _compute_overall_risk(
        self,
        consistency: ConsistencyScanResult,
        dep_drift: DepDriftReport,
        integration: IntegrityReport,
    ) -> float:
        """Compute weighted overall risk score."""
        consistency_risk = 100.0 - consistency.overall_score
        dep_risk = dep_drift.risk_score
        integration_risk = 100.0 - integration.health_score

        return (
            consistency_risk * 0.30
            + dep_risk * 0.35
            + integration_risk * 0.35
        )

    @staticmethod
    def _severity_to_risk(severity: str) -> float:
        """Convert severity string to risk score."""
        return {
            "INFO": 5.0,
            "LOW": 15.0,
            "MEDIUM": 35.0,
            "HIGH": 60.0,
            "CRITICAL": 90.0,
        }.get(severity, 25.0)
