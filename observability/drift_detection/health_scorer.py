"""
Architecture Health Scorer — Multi-dimensional health scoring for the system.

Computes overall architecture health based on consistency, dependency health,
integration integrity, and governance coverage. Provides a letter grade (A-F)
and actionable recommendations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from observability.drift_detection.consistency_scanner import ConsistencyScanResult
    from observability.drift_detection.drift_detector import UnifiedDriftReport

logger = logging.getLogger("observability.drift_detection.health_scorer")


@dataclass
class HealthDimension:
    """Score for a single health dimension."""
    name: str
    score: float = 0.0
    weight: float = 0.0
    weighted_score: float = 0.0
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 1),
            "weight": self.weight,
            "weighted_score": round(self.weighted_score, 2),
            "details": self.details,
        }


@dataclass
class HealthScore:
    """Complete architecture health assessment."""
    overall: float = 0.0
    grade: str = "F"
    dimensions: dict[str, HealthDimension] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall": round(self.overall, 1),
            "grade": self.grade,
            "dimensions": {k: v.to_dict() for k, v in self.dimensions.items()},
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
        }


class ArchitectureHealthScorer:
    """
    Computes overall architecture health from drift detection results.

    Dimensions and weights:
      - Consistency:           30%  (structural integrity of modules/imports)
      - Dependency Health:     25%  (absence of cycles, dead deps)
      - Integration Integrity: 25%  (bus connections working correctly)
      - Governance Coverage:   20%  (permission/policy completeness)
    """

    DIMENSION_WEIGHTS = {
        "consistency": 0.30,
        "dependency_health": 0.25,
        "integration_integrity": 0.25,
        "governance_coverage": 0.20,
    }

    def score(
        self,
        drift_report: "UnifiedDriftReport",
        consistency_result: "ConsistencyScanResult | None" = None,
    ) -> HealthScore:
        """Compute overall architecture health from drift analysis results."""
        from datetime import datetime, timezone

        logger.info("Computing architecture health score...")

        if consistency_result is None and drift_report.consistency:
            consistency_result = drift_report.consistency

        dimensions: dict[str, HealthDimension] = {}

        consistency_dim = self._score_consistency(consistency_result)
        dimensions["consistency"] = consistency_dim

        dep_dim = self._score_dependency_health(drift_report)
        dimensions["dependency_health"] = dep_dim

        integration_dim = self._score_integration_integrity(drift_report)
        dimensions["integration_integrity"] = integration_dim

        governance_dim = self._score_governance_coverage(drift_report)
        dimensions["governance_coverage"] = governance_dim

        overall = sum(d.weighted_score for d in dimensions.values())
        grade = self._score_to_grade(overall)
        recommendations = self._generate_recommendations(dimensions, drift_report)

        health = HealthScore(
            overall=overall,
            grade=grade,
            dimensions=dimensions,
            recommendations=recommendations,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        logger.info("Architecture health: %.1f (%s)", overall, grade)
        return health

    # ── Dimension Scorers ────────────────────────────────────────────────

    def _score_consistency(
        self, result: "ConsistencyScanResult | None"
    ) -> HealthDimension:
        """Score the consistency dimension."""
        weight = self.DIMENSION_WEIGHTS["consistency"]

        if result is None:
            return HealthDimension(
                name="consistency",
                score=50.0,
                weight=weight,
                weighted_score=50.0 * weight,
                details="No consistency data available",
            )

        score = result.overall_score
        return HealthDimension(
            name="consistency",
            score=score,
            weight=weight,
            weighted_score=score * weight,
            details=f"{len(result.issues)} issues detected across {result.modules_scanned} modules",
        )

    def _score_dependency_health(
        self, drift_report: "UnifiedDriftReport"
    ) -> HealthDimension:
        """Score the dependency health dimension."""
        weight = self.DIMENSION_WEIGHTS["dependency_health"]

        if drift_report.dependency_drift is None:
            return HealthDimension(
                name="dependency_health",
                score=50.0,
                weight=weight,
                weighted_score=50.0 * weight,
                details="No dependency drift data available",
            )

        dep = drift_report.dependency_drift
        score = max(0.0, 100.0 - dep.risk_score)

        details_parts: list[str] = []
        if dep.circular_deps:
            details_parts.append(f"{len(dep.circular_deps)} cycles")
        if dep.new_deps:
            details_parts.append(f"{len(dep.new_deps)} new deps")
        if dep.dead_deps:
            details_parts.append(f"{len(dep.dead_deps)} dead deps")

        details = ", ".join(details_parts) if details_parts else "No drift detected"

        return HealthDimension(
            name="dependency_health",
            score=score,
            weight=weight,
            weighted_score=score * weight,
            details=details,
        )

    def _score_integration_integrity(
        self, drift_report: "UnifiedDriftReport"
    ) -> HealthDimension:
        """Score the integration integrity dimension."""
        weight = self.DIMENSION_WEIGHTS["integration_integrity"]

        if drift_report.integration is None:
            return HealthDimension(
                name="integration_integrity",
                score=50.0,
                weight=weight,
                weighted_score=50.0 * weight,
                details="No integration data available",
            )

        integ = drift_report.integration
        score = integ.health_score

        details = (
            f"{len(integ.valid_connections)} valid, "
            f"{len(integ.broken_connections)} broken connections"
        )

        return HealthDimension(
            name="integration_integrity",
            score=score,
            weight=weight,
            weighted_score=score * weight,
            details=details,
        )

    def _score_governance_coverage(
        self, drift_report: "UnifiedDriftReport"
    ) -> HealthDimension:
        """Score the governance coverage dimension based on consistency issues."""
        weight = self.DIMENSION_WEIGHTS["governance_coverage"]

        score = 80.0

        if drift_report.consistency:
            gov_issues = [
                i for i in drift_report.consistency.issues
                if i.category in ("unregistered_subsystem", "unregistered_agent")
            ]
            score -= len(gov_issues) * 10

        score = max(0.0, min(100.0, score))

        return HealthDimension(
            name="governance_coverage",
            score=score,
            weight=weight,
            weighted_score=score * weight,
            details=f"Governance coverage assessment",
        )

    # ── Recommendations ──────────────────────────────────────────────────

    def _generate_recommendations(
        self,
        dimensions: dict[str, HealthDimension],
        drift_report: "UnifiedDriftReport",
    ) -> list[str]:
        """Generate actionable recommendations based on dimension scores."""
        recommendations: list[str] = []

        for name, dim in dimensions.items():
            if dim.score < 60:
                recommendations.append(
                    f"CRITICAL: {name} score is {dim.score:.0f}/100 — immediate attention required"
                )
            elif dim.score < 75:
                recommendations.append(
                    f"WARNING: {name} score is {dim.score:.0f}/100 — review recommended"
                )

        if drift_report.dependency_drift and drift_report.dependency_drift.circular_deps:
            recommendations.append(
                "Break circular dependencies to improve modularity and testability"
            )

        if drift_report.integration and drift_report.integration.broken_connections:
            broken_names = [b.name for b in drift_report.integration.broken_connections[:3]]
            recommendations.append(
                f"Fix broken bus connections: {', '.join(broken_names)}"
            )

        if drift_report.consistency and drift_report.consistency.overall_score < 80:
            recommendations.append(
                "Run a full consistency audit and address orphaned/broken modules"
            )

        if not recommendations:
            recommendations.append("Architecture health is good — no immediate actions needed")

        return recommendations

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _score_to_grade(score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
