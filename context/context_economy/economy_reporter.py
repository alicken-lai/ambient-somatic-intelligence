"""
Context Economy Reporter — Comprehensive reporting for the context economy.

Aggregates data from the CostAccountant, TokenEconomy, and EntropyManager
into unified reports with sections for budget utilization, cost analysis,
efficiency metrics, entropy analysis, and actionable recommendations.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ContextEconomyReport:
    """Full context economy report across all subsystems."""
    timestamp: float = field(default_factory=time.time)
    utilization: dict[str, Any] = field(default_factory=dict)
    costs: dict[str, Any] = field(default_factory=dict)
    entropy: dict[str, Any] = field(default_factory=dict)
    efficiency_score: float = 0.0
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
            "utilization": self.utilization,
            "costs": self.costs,
            "entropy": self.entropy,
            "efficiency_score": round(self.efficiency_score, 4),
            "recommendations": self.recommendations,
        }


class ContextEconomyReporter:
    """
    Generates comprehensive context economy reports.

    Usage:
        from context.context_economy.cost_accountant import ContextCostAccountant
        from context.context_economy.token_economy import TokenEconomy
        from context.context_economy.entropy_manager import ContextEntropyManager

        reporter = ContextEconomyReporter()
        report = reporter.generate_report(accountant, economy, entropy_mgr)
        print(reporter.to_markdown(report))
    """

    def generate_report(
        self,
        cost_accountant: Any,
        token_economy: Any,
        entropy_manager: Any,
        context_blocks: list[str] | None = None,
    ) -> ContextEconomyReport:
        """
        Generate a comprehensive context economy report.

        Sections:
          - Budget Utilization (from TokenEconomy)
          - Cost Analysis (from CostAccountant)
          - Entropy Analysis (from EntropyManager)
          - Efficiency Metrics (computed)
          - Recommendations (aggregated)
        """
        utilization = self._collect_utilization(token_economy)
        costs = self._collect_costs(cost_accountant)
        entropy = self._collect_entropy(entropy_manager, context_blocks)

        efficiency = self._compute_efficiency(utilization, costs, entropy)
        recommendations = self._aggregate_recommendations(
            utilization, costs, entropy, efficiency,
        )

        report = ContextEconomyReport(
            utilization=utilization,
            costs=costs,
            entropy=entropy,
            efficiency_score=efficiency,
            recommendations=recommendations,
        )

        logger.info(
            "Economy report generated: efficiency=%.3f, recommendations=%d",
            efficiency, len(recommendations),
        )
        return report

    def to_markdown(self, report: ContextEconomyReport) -> str:
        """Render a report as human-readable markdown."""
        ts = datetime.fromtimestamp(
            report.timestamp, tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S UTC")

        lines = [
            "# Context Economy Report",
            f"Generated: {ts}",
            f"Efficiency Score: **{report.efficiency_score:.1%}**",
            "",
            "## Budget Utilization",
        ]

        util = report.utilization
        lines.append(f"- System Budget: {util.get('system_budget', 'N/A')} tokens")
        lines.append(f"- Allocated: {util.get('total_allocated', 'N/A')} tokens")
        lines.append(f"- Used: {util.get('total_used', 'N/A')} tokens")
        lines.append(f"- Allocation Ratio: {util.get('allocation_ratio', 0):.1%}")
        lines.append(f"- Usage Ratio: {util.get('usage_ratio', 0):.1%}")
        lines.append("")

        lines.append("## Cost Analysis")
        costs = report.costs
        lines.append(f"- Total Tokens Consumed: {costs.get('total_tokens', 0)}")
        lines.append(f"- Record Count: {costs.get('record_count', 0)}")
        by_op = costs.get("by_operation", {})
        if by_op:
            lines.append("- By Operation:")
            for op, tokens in by_op.items():
                lines.append(f"  - {op}: {tokens} tokens")
        lines.append("")

        lines.append("## Entropy Analysis")
        ent = report.entropy
        lines.append(f"- Avg Entropy: {ent.get('avg_entropy', 0):.2f} bits")
        lines.append(f"- Redundancy: {ent.get('redundancy_score', 0):.1%}")
        lines.append(f"- Blocks Analyzed: {ent.get('block_count', 0)}")
        lines.append("")

        lines.append("## Recommendations")
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"{i}. {rec}")

        return "\n".join(lines)

    def to_dict(self, report: ContextEconomyReport) -> dict[str, Any]:
        """Return report as a JSON-serializable dict."""
        return report.to_dict()

    def _collect_utilization(self, token_economy: Any) -> dict[str, Any]:
        """Collect utilization data from TokenEconomy."""
        try:
            return token_economy.get_utilization()
        except Exception:
            logger.warning("Failed to collect utilization data")
            return {}

    def _collect_costs(self, cost_accountant: Any) -> dict[str, Any]:
        """Collect cost data from CostAccountant."""
        try:
            summary = cost_accountant.get_system_costs()
            return summary.to_dict()
        except Exception:
            logger.warning("Failed to collect cost data")
            return {}

    def _collect_entropy(
        self,
        entropy_manager: Any,
        context_blocks: list[str] | None,
    ) -> dict[str, Any]:
        """Collect entropy data from EntropyManager."""
        try:
            report = entropy_manager.get_entropy_report(context_blocks)
            return report.to_dict()
        except Exception:
            logger.warning("Failed to collect entropy data")
            return {}

    def _compute_efficiency(
        self,
        utilization: dict[str, Any],
        costs: dict[str, Any],
        entropy: dict[str, Any],
    ) -> float:
        """
        Compute composite efficiency score from subsystem metrics.

        Factors:
          - Budget utilization efficiency (not too high, not too low)
          - Cost efficiency score
          - Low redundancy is good
        """
        usage_ratio = utilization.get("usage_ratio", 0.5)
        usage_eff = 1.0 - abs(usage_ratio - 0.7) / 0.7

        cost_eff = costs.get("efficiency_score", 0.0)

        redundancy = entropy.get("redundancy_score", 0.0)
        entropy_eff = 1.0 - redundancy

        score = (
            0.40 * max(0.0, usage_eff)
            + 0.35 * min(cost_eff, 1.0)
            + 0.25 * entropy_eff
        )

        return max(0.0, min(1.0, score))

    def _aggregate_recommendations(
        self,
        utilization: dict[str, Any],
        costs: dict[str, Any],
        entropy: dict[str, Any],
        efficiency: float,
    ) -> list[str]:
        """Aggregate recommendations from all subsystems."""
        recs: list[str] = []

        alloc_ratio = utilization.get("allocation_ratio", 0)
        usage_ratio = utilization.get("usage_ratio", 0)

        if alloc_ratio > 0.9:
            recs.append(
                f"System budget nearly exhausted ({alloc_ratio:.0%} allocated) — "
                f"consider increasing system budget or releasing unused allocations"
            )
        elif alloc_ratio < 0.3 and utilization.get("agent_count", 0) > 0:
            recs.append(
                f"Low allocation ratio ({alloc_ratio:.0%}) — budget may be "
                f"oversized for current workload"
            )

        if usage_ratio > 0.9:
            recs.append(
                "High usage ratio — agents are consuming most of their allocation"
            )
        elif usage_ratio < 0.2 and usage_ratio > 0:
            recs.append(
                "Low usage ratio — consider reducing allocations to free budget"
            )

        entropy_recs = entropy.get("recommendations", [])
        recs.extend(entropy_recs)

        if efficiency < 0.3:
            recs.append(
                f"Overall efficiency is low ({efficiency:.0%}) — review cost "
                f"distribution and retrieval utility"
            )

        if not recs:
            recs.append("Context economy is operating efficiently")

        return recs
