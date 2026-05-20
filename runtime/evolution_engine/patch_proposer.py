"""
Patch Proposer — Generate refactoring patch proposals.

Creates structured descriptions of proposed changes based on:
  - Detected drift between current and expected behavior
  - Optimization opportunities identified by analysis
  - Patterns learned from system operation

IMPORTANT: All proposals are descriptions, NOT actual code patches.
The system proposes; humans decide. No auto-deployment.

Each patch proposal includes:
  - What to change and why
  - Expected impact
  - Risk assessment
  - Reversibility analysis
"""

from __future__ import annotations

try:
    from governance.audit_log import GovernanceAuditLog
except ImportError:  # pragma: no cover
    GovernanceAuditLog = None  # type: ignore[misc, assignment]

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PatchType(str, Enum):
    """Types of proposed patches."""
    FIX = "fix"
    OPTIMIZE = "optimize"
    REFACTOR = "refactor"
    EVOLVE = "evolve"


@dataclass
class PatchProposal:
    """A structured proposal for a system change."""
    patch_id: str = field(default_factory=lambda: f"patch_{uuid.uuid4().hex[:12]}")
    title: str = ""
    description: str = ""
    type: PatchType = PatchType.REFACTOR
    target_module: str = ""
    changes_description: str = ""
    estimated_impact: dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0
    reversibility: str = "full"
    dependencies: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "patch_id": self.patch_id,
            "title": self.title,
            "description": self.description,
            "type": self.type.value,
            "target_module": self.target_module,
            "changes_description": self.changes_description,
            "estimated_impact": self.estimated_impact,
            "risk_score": round(self.risk_score, 4),
            "reversibility": self.reversibility,
            "dependencies": self.dependencies,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


class PatchProposer:
    """
    Generates refactoring patch proposals from system analysis.

    Creates structured, human-readable proposals based on drift reports,
    optimization results, and learned patterns. All proposals are
    descriptive — they describe WHAT to change and WHY, but do not
    contain executable code.

    Usage:
        proposer = PatchProposer()

        patches = proposer.propose_from_drift({
            "drift_type": "performance_degradation",
            "module": "memory/memory_kernel.py",
            "current_metric": 150,
            "expected_metric": 50,
            "evidence": "Recall latency tripled over last 24h",
        })

        for patch in patches:
            print(f"{patch.title}: {patch.description}")
    """

    def __init__(self, risk_threshold: float = 0.8):
        self._proposals: list[PatchProposal] = []
        self._risk_threshold = risk_threshold

    def propose_from_drift(self, drift_report: dict[str, Any]) -> list[PatchProposal]:
        """
        Generate patches to correct detected drift.

        Args:
            drift_report: Dict containing drift_type, module, current/expected metrics,
                         and evidence of the drift.

        Returns:
            List of PatchProposals addressing the drift
        """
        proposals: list[PatchProposal] = []
        drift_type = drift_report.get("drift_type", "unknown")
        module = drift_report.get("module", "unknown")
        evidence = drift_report.get("evidence", "")

        if drift_type == "performance_degradation":
            proposals.append(self._propose_performance_fix(drift_report))
        elif drift_type == "memory_pressure":
            proposals.append(self._propose_memory_optimization(drift_report))
        elif drift_type == "governance_bottleneck":
            proposals.append(self._propose_governance_tuning(drift_report))
        elif drift_type == "error_rate_increase":
            proposals.append(self._propose_error_mitigation(drift_report))
        else:
            proposals.append(PatchProposal(
                title=f"Address {drift_type} drift in {module}",
                description=f"Drift detected: {evidence}",
                type=PatchType.FIX,
                target_module=module,
                changes_description=(
                    f"Investigate and remediate {drift_type} drift. "
                    f"Current behavior deviates from expected baseline."
                ),
                estimated_impact={"reliability": "improved", "scope": "targeted"},
                risk_score=self._estimate_risk(drift_report),
                reversibility="full",
            ))

        for proposal in proposals:
            self._proposals.append(proposal)

        logger.info("Generated %d patches from drift report: %s", len(proposals), drift_type)
        return proposals

    def propose_from_optimization(self, optimization_result: dict[str, Any]) -> list[PatchProposal]:
        """
        Generate patches from optimization analysis results.

        Args:
            optimization_result: Dict with optimization_type, target, current_value,
                                projected_value, and approach description.

        Returns:
            List of PatchProposals for the optimization
        """
        opt_type = optimization_result.get("optimization_type", "general")
        target = optimization_result.get("target", "unknown")
        approach = optimization_result.get("approach", "")
        current = optimization_result.get("current_value", 0)
        projected = optimization_result.get("projected_value", 0)

        proposal = PatchProposal(
            title=f"Optimize: {opt_type} for {target}",
            description=(
                f"Optimization opportunity identified in {target}. "
                f"Current: {current}, Projected after change: {projected}."
            ),
            type=PatchType.OPTIMIZE,
            target_module=target,
            changes_description=approach or f"Apply {opt_type} optimization to {target}.",
            estimated_impact={
                "current_value": current,
                "projected_value": projected,
                "improvement_pct": round(
                    ((projected - current) / current * 100) if current else 0, 1
                ),
            },
            risk_score=self._estimate_optimization_risk(optimization_result),
            reversibility="full",
            dependencies=optimization_result.get("dependencies", []),
        )

        self._proposals.append(proposal)
        logger.info("Generated optimization patch: %s", proposal.title)
        return [proposal]

    def propose_from_patterns(self, patterns: list[dict[str, Any]]) -> list[PatchProposal]:
        """
        Generate patches based on learned operational patterns.

        Args:
            patterns: List of pattern dicts with pattern_type, description,
                     frequency, affected_modules, and suggested_action.

        Returns:
            List of PatchProposals derived from patterns
        """
        proposals: list[PatchProposal] = []

        for pattern in patterns:
            pattern_type = pattern.get("pattern_type", "unknown")
            description = pattern.get("description", "")
            affected = pattern.get("affected_modules", [])
            action = pattern.get("suggested_action", "")
            frequency = pattern.get("frequency", 0)

            proposal = PatchProposal(
                title=f"Pattern-driven: {pattern_type}",
                description=(
                    f"Recurring pattern detected ({frequency}x): {description}. "
                    f"Affects: {', '.join(affected) if affected else 'system-wide'}."
                ),
                type=PatchType.EVOLVE,
                target_module=affected[0] if affected else "system",
                changes_description=action or f"Adapt system to address {pattern_type} pattern.",
                estimated_impact={
                    "pattern_frequency": frequency,
                    "affected_modules": affected,
                    "expected_outcome": "reduced pattern recurrence",
                },
                risk_score=self._estimate_pattern_risk(pattern),
                reversibility="full" if len(affected) <= 2 else "partial",
                dependencies=[m for m in affected[1:]] if len(affected) > 1 else [],
            )

            proposals.append(proposal)
            self._proposals.append(proposal)

        logger.info("Generated %d patches from %d patterns", len(proposals), len(patterns))
        return proposals

    def get_all_proposals(self) -> list[dict[str, Any]]:
        """Get all generated proposals."""
        return [p.to_dict() for p in self._proposals]

    def get_proposal(self, patch_id: str) -> PatchProposal | None:
        """Retrieve a specific proposal by ID."""
        for p in self._proposals:
            if p.patch_id == patch_id:
                return p
        return None

    def _propose_performance_fix(self, drift_report: dict[str, Any]) -> PatchProposal:
        """Generate a performance-focused fix proposal."""
        module = drift_report.get("module", "unknown")
        current = drift_report.get("current_metric", 0)
        expected = drift_report.get("expected_metric", 0)

        return PatchProposal(
            title=f"Fix performance degradation in {module}",
            description=(
                f"Performance has degraded: current={current}, expected={expected}. "
                f"Evidence: {drift_report.get('evidence', 'N/A')}"
            ),
            type=PatchType.FIX,
            target_module=module,
            changes_description=(
                f"Profile {module} to identify hotspots. "
                f"Consider: caching, batch processing, reducing allocation pressure, "
                f"or restructuring data access patterns."
            ),
            estimated_impact={
                "latency_reduction": f"{current - expected}ms estimated",
                "scope": "targeted",
            },
            risk_score=0.3,
            reversibility="full",
        )

    def _propose_memory_optimization(self, drift_report: dict[str, Any]) -> PatchProposal:
        """Generate a memory-pressure mitigation proposal."""
        module = drift_report.get("module", "memory")

        return PatchProposal(
            title=f"Reduce memory pressure in {module}",
            description=f"Memory pressure detected: {drift_report.get('evidence', 'N/A')}",
            type=PatchType.OPTIMIZE,
            target_module=module,
            changes_description=(
                "Consider: increasing TTL decay rate, enabling more aggressive compression, "
                "reducing layer capacity, or implementing LRU eviction for cold records."
            ),
            estimated_impact={"memory_reduction": "20-40% estimated", "scope": "memory layer"},
            risk_score=0.4,
            reversibility="full",
        )

    def _propose_governance_tuning(self, drift_report: dict[str, Any]) -> PatchProposal:
        """Generate a governance tuning proposal."""
        if GovernanceAuditLog is not None:
            try:
                from governance.policy_engine import RiskLevel

                GovernanceAuditLog().record_decision(
                    action="patch_proposer:governance_tuning",
                    risk=RiskLevel.ALLOW,
                    reason="evolution_engine proposal trace",
                    agent_id="patch_proposer",
                    metadata={"drift": drift_report},
                )
            except Exception:
                pass
        return PatchProposal(
            title="Tune governance gate thresholds",
            description=f"Governance bottleneck detected: {drift_report.get('evidence', 'N/A')}",
            type=PatchType.OPTIMIZE,
            target_module="governance",
            changes_description=(
                "Consider: caching frequent check results, relaxing low-risk action policies, "
                "implementing batch-checking for related actions, or adding async pre-approval."
            ),
            estimated_impact={"latency_reduction": "significant", "scope": "governance layer"},
            risk_score=0.5,
            reversibility="full",
        )

    def _propose_error_mitigation(self, drift_report: dict[str, Any]) -> PatchProposal:
        """Generate an error-rate mitigation proposal."""
        module = drift_report.get("module", "unknown")

        return PatchProposal(
            title=f"Mitigate error rate increase in {module}",
            description=f"Error rate has increased: {drift_report.get('evidence', 'N/A')}",
            type=PatchType.FIX,
            target_module=module,
            changes_description=(
                "Investigate error root cause. Consider: adding retry logic, "
                "improving input validation, adding circuit breakers, or "
                "implementing graceful degradation for the affected path."
            ),
            estimated_impact={"error_reduction": "estimated 50-80%", "scope": "targeted"},
            risk_score=0.35,
            reversibility="full",
        )

    def _estimate_risk(self, drift_report: dict[str, Any]) -> float:
        """Estimate risk score for a drift-based patch."""
        base_risk = 0.3
        if "critical" in drift_report.get("drift_type", "").lower():
            base_risk += 0.3
        if drift_report.get("affects_production", False):
            base_risk += 0.2
        return min(1.0, base_risk)

    def _estimate_optimization_risk(self, opt_result: dict[str, Any]) -> float:
        """Estimate risk score for an optimization patch."""
        base_risk = 0.2
        if opt_result.get("requires_migration", False):
            base_risk += 0.3
        deps = opt_result.get("dependencies", [])
        base_risk += len(deps) * 0.05
        return min(1.0, base_risk)

    def _estimate_pattern_risk(self, pattern: dict[str, Any]) -> float:
        """Estimate risk score for a pattern-based patch."""
        affected_count = len(pattern.get("affected_modules", []))
        base_risk = 0.2 + (affected_count * 0.1)
        return min(1.0, base_risk)
