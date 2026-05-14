"""
Efficiency Reporter — Generate comprehensive execution efficiency reports.

Combines pattern analysis, optimization proposals, and incident data into
structured reports for system operators and automated decision-making.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from memory.evolution.incident_learner import IncidentAnalysis
from memory.evolution.optimization_proposer import OptimizationProposal
from memory.evolution.pattern_miner import FailurePattern, SuccessPattern

logger = logging.getLogger(__name__)


@dataclass
class ReportSection:
    """A section within an efficiency report."""
    title: str
    content: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "data": self.data,
        }


@dataclass
class EfficiencyReport:
    """A comprehensive efficiency report with multiple analysis sections."""
    timestamp: str
    summary: str
    patterns_found: int
    proposals_generated: int
    risk_score: float
    sections: list[ReportSection]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "summary": self.summary,
            "patterns_found": self.patterns_found,
            "proposals_generated": self.proposals_generated,
            "risk_score": round(self.risk_score, 3),
            "sections": [s.to_dict() for s in self.sections],
        }

    def to_markdown(self) -> str:
        """Render the report as human-readable Markdown."""
        lines: list[str] = []
        lines.append("# Efficiency Report")
        lines.append(f"\n**Generated:** {self.timestamp}")
        lines.append(f"\n## Executive Summary\n\n{self.summary}")
        lines.append(f"\n- Patterns found: {self.patterns_found}")
        lines.append(f"- Proposals generated: {self.proposals_generated}")
        lines.append(f"- Risk score: {self.risk_score:.2f}/1.00")

        for section in self.sections:
            lines.append(f"\n## {section.title}\n")
            lines.append(section.content)
            if section.data:
                for key, value in section.data.items():
                    if isinstance(value, list):
                        lines.append(f"\n### {key}")
                        for item in value[:10]:
                            if isinstance(item, dict):
                                lines.append(f"- {item}")
                            else:
                                lines.append(f"- {item}")
                    else:
                        lines.append(f"- **{key}:** {value}")

        return "\n".join(lines)


class EfficiencyReporter:
    """
    Generate comprehensive execution efficiency reports.

    Aggregates insights from pattern mining, optimization proposals, and
    incident analysis into structured reports.

    Usage:
        reporter = EfficiencyReporter()
        report = reporter.generate_report(
            success_patterns, failure_patterns, proposals, incident_analysis
        )
        print(report.to_markdown())
    """

    def generate_report(
        self,
        success_patterns: list[SuccessPattern] | None = None,
        failure_patterns: list[FailurePattern] | None = None,
        proposals: list[OptimizationProposal] | None = None,
        incident_analysis: IncidentAnalysis | None = None,
    ) -> EfficiencyReport:
        """
        Generate a comprehensive efficiency report.

        Sections:
          - Executive Summary
          - Pattern Analysis (success + failure patterns)
          - Failure Analysis (detailed failure breakdown)
          - Optimization Proposals (ranked proposals)
          - Risk Assessment (overall system risk)
        """
        success_patterns = success_patterns or []
        failure_patterns = failure_patterns or []
        proposals = proposals or []

        sections: list[ReportSection] = []

        sections.append(self._build_pattern_section(success_patterns, failure_patterns))
        sections.append(self._build_failure_section(failure_patterns))
        sections.append(self._build_proposals_section(proposals))
        sections.append(self._build_risk_section(
            failure_patterns, proposals, incident_analysis
        ))

        risk_score = self._compute_risk_score(failure_patterns, incident_analysis)
        total_patterns = len(success_patterns) + len(failure_patterns)

        summary = self._generate_summary(
            success_patterns, failure_patterns, proposals, risk_score
        )

        report = EfficiencyReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            summary=summary,
            patterns_found=total_patterns,
            proposals_generated=len(proposals),
            risk_score=risk_score,
            sections=sections,
        )

        logger.info(
            "Generated efficiency report: %d patterns, %d proposals, risk=%.2f",
            total_patterns, len(proposals), risk_score
        )
        return report

    def _build_pattern_section(
        self,
        success_patterns: list[SuccessPattern],
        failure_patterns: list[FailurePattern],
    ) -> ReportSection:
        """Build the Pattern Analysis section."""
        content_lines: list[str] = []

        if success_patterns:
            content_lines.append(f"Identified {len(success_patterns)} success patterns:")
            for p in success_patterns[:5]:
                content_lines.append(
                    f"  - {p.description} (freq={p.frequency}, "
                    f"success={p.success_rate:.0%}, confidence={p.confidence:.2f})"
                )
        else:
            content_lines.append("No success patterns identified.")

        if failure_patterns:
            content_lines.append(f"\nIdentified {len(failure_patterns)} failure patterns:")
            for p in failure_patterns[:5]:
                content_lines.append(
                    f"  - {p.description} (freq={p.frequency}, "
                    f"severity={p.severity})"
                )
        else:
            content_lines.append("\nNo failure patterns identified.")

        return ReportSection(
            title="Pattern Analysis",
            content="\n".join(content_lines),
            data={
                "success_count": len(success_patterns),
                "failure_count": len(failure_patterns),
                "top_success": [p.to_dict() for p in success_patterns[:3]],
                "top_failure": [p.to_dict() for p in failure_patterns[:3]],
            },
        )

    def _build_failure_section(
        self, failure_patterns: list[FailurePattern]
    ) -> ReportSection:
        """Build the Failure Analysis section."""
        if not failure_patterns:
            return ReportSection(
                title="Failure Analysis",
                content="No failure patterns detected — system operating normally.",
                data={},
            )

        by_type: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        all_causes: list[str] = []

        for p in failure_patterns:
            by_type[p.failure_type] = by_type.get(p.failure_type, 0) + p.frequency
            by_severity[p.severity] = by_severity.get(p.severity, 0) + 1
            all_causes.extend(p.potential_causes)

        content_lines = [
            f"Total failure patterns: {len(failure_patterns)}",
            f"By type: {by_type}",
            f"By severity: {by_severity}",
        ]

        unique_causes = list(set(all_causes))
        if unique_causes:
            content_lines.append(f"Root causes identified: {len(unique_causes)}")

        return ReportSection(
            title="Failure Analysis",
            content="\n".join(content_lines),
            data={
                "by_type": by_type,
                "by_severity": by_severity,
                "root_causes": unique_causes[:10],
            },
        )

    def _build_proposals_section(
        self, proposals: list[OptimizationProposal]
    ) -> ReportSection:
        """Build the Optimization Proposals section."""
        if not proposals:
            return ReportSection(
                title="Optimization Proposals",
                content="No optimization proposals generated — system is performing well.",
                data={},
            )

        by_type: dict[str, int] = {}
        by_impact: dict[str, int] = {}
        for p in proposals:
            by_type[p.type.value] = by_type.get(p.type.value, 0) + 1
            by_impact[p.estimated_impact.value] = by_impact.get(p.estimated_impact.value, 0) + 1

        content_lines = [
            f"Generated {len(proposals)} optimization proposals:",
            f"By type: {by_type}",
            f"By impact: {by_impact}",
            "",
            "Top proposals:",
        ]
        for p in proposals[:5]:
            content_lines.append(f"  - [{p.estimated_impact.value.upper()}] {p.title}")

        return ReportSection(
            title="Optimization Proposals",
            content="\n".join(content_lines),
            data={
                "by_type": by_type,
                "by_impact": by_impact,
                "proposals": [p.to_dict() for p in proposals[:10]],
            },
        )

    def _build_risk_section(
        self,
        failure_patterns: list[FailurePattern],
        proposals: list[OptimizationProposal],
        incident_analysis: IncidentAnalysis | None,
    ) -> ReportSection:
        """Build the Risk Assessment section."""
        risk_factors: list[str] = []

        critical_failures = [p for p in failure_patterns if p.severity == "critical"]
        if critical_failures:
            risk_factors.append(
                f"{len(critical_failures)} critical failure patterns detected"
            )

        high_impact = [
            p for p in proposals if p.estimated_impact.value == "high"
        ]
        if high_impact:
            risk_factors.append(
                f"{len(high_impact)} high-impact optimizations pending"
            )

        if incident_analysis and incident_analysis.total_incidents > 10:
            risk_factors.append(
                f"High incident count: {incident_analysis.total_incidents}"
            )

        if not risk_factors:
            risk_factors.append("No significant risk factors identified")

        content = "Risk factors:\n" + "\n".join(f"  - {r}" for r in risk_factors)

        return ReportSection(
            title="Risk Assessment",
            content=content,
            data={
                "risk_factors": risk_factors,
                "critical_failure_count": len(critical_failures),
                "pending_high_impact_proposals": len(high_impact),
            },
        )

    def _compute_risk_score(
        self,
        failure_patterns: list[FailurePattern],
        incident_analysis: IncidentAnalysis | None,
    ) -> float:
        """
        Compute an overall risk score (0.0 = no risk, 1.0 = maximum risk).

        Factors: severity of failures, frequency, and incident volume.
        """
        score = 0.0

        severity_weights = {"critical": 0.3, "high": 0.2, "medium": 0.1, "low": 0.05}
        for p in failure_patterns:
            score += severity_weights.get(p.severity, 0.05)

        if incident_analysis:
            incident_factor = min(incident_analysis.total_incidents / 20.0, 0.3)
            score += incident_factor

        return min(1.0, score)

    def _generate_summary(
        self,
        success_patterns: list[SuccessPattern],
        failure_patterns: list[FailurePattern],
        proposals: list[OptimizationProposal],
        risk_score: float,
    ) -> str:
        """Generate executive summary text."""
        parts: list[str] = []

        if success_patterns:
            top = success_patterns[0]
            parts.append(
                f"Found {len(success_patterns)} reusable success patterns "
                f"(best: {top.success_rate:.0%} success rate, "
                f"confidence {top.confidence:.2f})."
            )

        if failure_patterns:
            critical = [p for p in failure_patterns if p.severity in ("critical", "high")]
            parts.append(
                f"Detected {len(failure_patterns)} failure patterns "
                f"({len(critical)} high/critical severity)."
            )

        if proposals:
            high = [p for p in proposals if p.estimated_impact.value == "high"]
            parts.append(
                f"Generated {len(proposals)} optimization proposals "
                f"({len(high)} high-impact)."
            )

        if risk_score > 0.6:
            parts.append("⚠ Overall risk is ELEVATED — immediate attention recommended.")
        elif risk_score > 0.3:
            parts.append("Risk is MODERATE — scheduled review recommended.")
        else:
            parts.append("Risk is LOW — system operating within expected parameters.")

        return " ".join(parts) if parts else "No data available for analysis."
