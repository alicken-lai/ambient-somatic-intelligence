"""
Optimization Proposer — Generate candidate optimization proposals from mined patterns.

Converts success/failure patterns into actionable proposals for system improvement,
including scheduler refinements, memory configuration changes, and workflow templates.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from memory.evolution.pattern_miner import SuccessPattern, FailurePattern

logger = logging.getLogger(__name__)


class ProposalType(str, Enum):
    TEMPLATE = "template"
    PREVENTION = "prevention"
    REFINEMENT = "refinement"
    EFFICIENCY = "efficiency"


class ImpactLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class OptimizationProposal:
    """A concrete optimization proposal with evidence and risk assessment."""
    proposal_id: str
    title: str
    description: str
    type: ProposalType
    estimated_impact: ImpactLevel
    evidence: list[str]
    implementation_hint: str
    risk_assessment: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "title": self.title,
            "description": self.description,
            "type": self.type.value,
            "estimated_impact": self.estimated_impact.value,
            "evidence": self.evidence,
            "implementation_hint": self.implementation_hint,
            "risk_assessment": self.risk_assessment,
        }


@dataclass
class SchedulerRefinement:
    """A proposed scheduler configuration change."""
    parameter: str
    current_value: Any
    proposed_value: Any
    reason: str
    expected_improvement: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter": self.parameter,
            "current_value": self.current_value,
            "proposed_value": self.proposed_value,
            "reason": self.reason,
            "expected_improvement": self.expected_improvement,
        }


@dataclass
class MemoryOptimization:
    """A proposed memory configuration change."""
    parameter: str
    layer: str
    current_value: Any
    proposed_value: Any
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter": self.parameter,
            "layer": self.layer,
            "current_value": self.current_value,
            "proposed_value": self.proposed_value,
            "reason": self.reason,
        }


class OptimizationProposer:
    """
    Generate candidate optimization proposals from mined patterns.

    Transforms pattern analysis results into actionable, evidence-backed
    proposals for system improvement.

    Usage:
        proposer = OptimizationProposer()
        proposals = proposer.propose_from_patterns(success_patterns, failure_patterns)
        scheduler_refs = proposer.propose_scheduler_refinements(execution_stats)
        memory_opts = proposer.propose_memory_optimizations(memory_stats)
    """

    def propose_from_patterns(
        self,
        success_patterns: list[SuccessPattern],
        failure_patterns: list[FailurePattern],
    ) -> list[OptimizationProposal]:
        """
        Generate proposals from success and failure patterns.

        For each success pattern: suggest codifying as reusable template.
        For each failure pattern: suggest preventive measures.
        """
        proposals: list[OptimizationProposal] = []

        for pattern in success_patterns:
            if pattern.confidence < 0.5:
                continue

            impact = self._assess_impact_from_success(pattern)
            proposals.append(OptimizationProposal(
                proposal_id=f"opt-{uuid.uuid4().hex[:8]}",
                title=f"Codify pattern: {pattern.description[:60]}",
                description=(
                    f"Pattern observed {pattern.frequency} times with "
                    f"{pattern.success_rate:.0%} success rate. "
                    f"Codify as reusable orchestration template."
                ),
                type=ProposalType.TEMPLATE,
                estimated_impact=impact,
                evidence=[
                    f"Frequency: {pattern.frequency}",
                    f"Success rate: {pattern.success_rate:.1%}",
                    f"Avg duration: {pattern.avg_duration:.0f}ms",
                    f"Agents: {', '.join(pattern.agents_involved[:3])}",
                ],
                implementation_hint=(
                    "Extract the task sequence from this pattern and register it "
                    "as an OrchestrationTemplate for future reuse."
                ),
                risk_assessment=self._template_risk(pattern),
            ))

        for pattern in failure_patterns:
            impact = self._assess_impact_from_failure(pattern)
            proposals.append(OptimizationProposal(
                proposal_id=f"opt-{uuid.uuid4().hex[:8]}",
                title=f"Prevent: {pattern.description[:60]}",
                description=(
                    f"Failure pattern '{pattern.failure_type}' occurred {pattern.frequency} times "
                    f"affecting {len(pattern.agents_affected)} agents. "
                    f"Severity: {pattern.severity}."
                ),
                type=ProposalType.PREVENTION,
                estimated_impact=impact,
                evidence=[
                    f"Frequency: {pattern.frequency}",
                    f"Type: {pattern.failure_type}",
                    f"Severity: {pattern.severity}",
                    f"Affected agents: {', '.join(pattern.agents_affected[:3])}",
                ] + [f"Cause: {c}" for c in pattern.potential_causes[:2]],
                implementation_hint=self._prevention_hint(pattern),
                risk_assessment=self._prevention_risk(pattern),
            ))

        proposals.sort(key=lambda p: (
            {"high": 3, "medium": 2, "low": 1}[p.estimated_impact.value],
        ), reverse=True)

        logger.info("Generated %d optimization proposals", len(proposals))
        return proposals

    def propose_scheduler_refinements(
        self, execution_stats: dict[str, Any]
    ) -> list[SchedulerRefinement]:
        """
        Suggest scheduler configuration changes based on execution statistics.

        Analyzes whether max_concurrent, timeouts, and retry policies are optimal
        given observed execution patterns.
        """
        refinements: list[SchedulerRefinement] = []

        avg_duration = execution_stats.get("avg_duration_ms", 0)
        total_tasks = execution_stats.get("total_executions", 0)
        success_rate = execution_stats.get("success_rate", 1.0)
        task_types = execution_stats.get("task_types", {})

        if avg_duration > 60000 and total_tasks >= 5:
            refinements.append(SchedulerRefinement(
                parameter="task_timeout_seconds",
                current_value=120.0,
                proposed_value=max(180.0, avg_duration / 1000 * 2.5),
                reason=f"Average task duration ({avg_duration:.0f}ms) is high relative to timeout",
                expected_improvement="Fewer timeout-related failures",
            ))

        if avg_duration < 5000 and total_tasks >= 10:
            refinements.append(SchedulerRefinement(
                parameter="task_timeout_seconds",
                current_value=120.0,
                proposed_value=30.0,
                reason=f"Tasks are fast (avg {avg_duration:.0f}ms) — tighter timeout catches hangs sooner",
                expected_improvement="Faster detection of hung tasks",
            ))

        if success_rate < 0.7 and total_tasks >= 5:
            refinements.append(SchedulerRefinement(
                parameter="max_concurrent",
                current_value=5,
                proposed_value=3,
                reason=f"Low success rate ({success_rate:.1%}) — reduce concurrency to isolate failures",
                expected_improvement="Better failure isolation and debugging",
            ))
        elif success_rate > 0.95 and total_tasks >= 10 and len(task_types) > 3:
            refinements.append(SchedulerRefinement(
                parameter="max_concurrent",
                current_value=5,
                proposed_value=8,
                reason=f"High success rate ({success_rate:.1%}) with diverse tasks — safe to increase parallelism",
                expected_improvement="Higher throughput for parallel-safe workloads",
            ))

        if success_rate < 0.5:
            refinements.append(SchedulerRefinement(
                parameter="fail_fast",
                current_value=True,
                proposed_value=False,
                reason="Very low success rate — disable fail_fast to gather more failure data",
                expected_improvement="Better understanding of failure distribution",
            ))

        return refinements

    def propose_memory_optimizations(
        self, memory_stats: dict[str, Any]
    ) -> list[MemoryOptimization]:
        """
        Suggest memory configuration changes based on layer statistics.

        Analyzes whether TTLs are optimal, dedup frequency is right, and
        whether layers are balanced.
        """
        optimizations: list[MemoryOptimization] = []
        layers = memory_stats.get("layers", {})
        total_records = memory_stats.get("total_records", 0)

        if total_records == 0:
            return optimizations

        for layer_name, stats in layers.items():
            count = stats.get("count", 0)
            expired = stats.get("expired", 0)
            avg_age = stats.get("avg_age_hours", 0)
            ttl_hours = stats.get("ttl_hours", 0)

            if count > 0 and expired / count > 0.3:
                optimizations.append(MemoryOptimization(
                    parameter="ttl_sweep_frequency",
                    layer=layer_name,
                    current_value="on_demand",
                    proposed_value="hourly",
                    reason=f"{expired}/{count} records ({expired/count:.0%}) are expired in '{layer_name}' — sweep more often",
                ))

            if ttl_hours > 0 and avg_age > 0 and avg_age > ttl_hours * 0.8:
                optimizations.append(MemoryOptimization(
                    parameter="ttl_policy",
                    layer=layer_name,
                    current_value=f"{ttl_hours:.0f}h",
                    proposed_value=f"{ttl_hours * 1.5:.0f}h",
                    reason=f"Average age ({avg_age:.0f}h) is close to TTL ({ttl_hours:.0f}h) — records may be expiring before useful",
                ))

        layer_counts = {name: s.get("count", 0) for name, s in layers.items()}
        if layer_counts:
            max_layer = max(layer_counts, key=lambda k: layer_counts[k])
            max_count = layer_counts[max_layer]
            if max_count > total_records * 0.7 and total_records > 50:
                optimizations.append(MemoryOptimization(
                    parameter="layer_balance",
                    layer=max_layer,
                    current_value=f"{max_count}/{total_records}",
                    proposed_value="better distribution",
                    reason=f"Layer '{max_layer}' holds {max_count/total_records:.0%} of all records — consider classification tuning",
                ))

        entropy = memory_stats.get("entropy", 0)
        if entropy < 1.0 and total_records > 50:
            optimizations.append(MemoryOptimization(
                parameter="classification_diversity",
                layer="all",
                current_value=f"entropy={entropy:.2f}",
                proposed_value="entropy≥1.5",
                reason="Low entropy suggests records cluster in few layers — classification may need broadening",
            ))

        return optimizations

    def _assess_impact_from_success(self, pattern: SuccessPattern) -> ImpactLevel:
        """Assess potential impact of codifying a success pattern."""
        if pattern.frequency >= 10 and pattern.confidence >= 0.8:
            return ImpactLevel.HIGH
        if pattern.frequency >= 5 or pattern.confidence >= 0.7:
            return ImpactLevel.MEDIUM
        return ImpactLevel.LOW

    def _assess_impact_from_failure(self, pattern: FailurePattern) -> ImpactLevel:
        """Assess potential impact of preventing a failure pattern."""
        if pattern.severity == "critical":
            return ImpactLevel.HIGH
        if pattern.severity == "high" or pattern.frequency >= 5:
            return ImpactLevel.HIGH
        if pattern.severity == "medium" or pattern.frequency >= 3:
            return ImpactLevel.MEDIUM
        return ImpactLevel.LOW

    def _template_risk(self, pattern: SuccessPattern) -> str:
        """Assess risk of codifying a pattern as template."""
        if pattern.confidence < 0.6:
            return "Medium — pattern confidence is moderate, may not generalize well"
        if len(pattern.agents_involved) == 1:
            return "Low-Medium — pattern only observed in one agent, may be context-specific"
        return "Low — high confidence pattern observed across multiple agents"

    def _prevention_risk(self, pattern: FailurePattern) -> str:
        """Assess risk of implementing a preventive measure."""
        if pattern.severity == "critical":
            return "Low — critical failures justify aggressive prevention"
        if len(pattern.agents_affected) >= 3:
            return "Low-Medium — broad impact justifies intervention, but test carefully"
        return "Medium — limited data; monitor after implementation"

    def _prevention_hint(self, pattern: FailurePattern) -> str:
        """Generate implementation hint for a preventive measure."""
        hints = {
            "timeout": "Increase timeout limits or add pre-flight health checks before long operations",
            "permission_denied": "Review agent permission matrix; add explicit grants or remove unnecessary restrictions",
            "resource_not_found": "Add dependency validation before task execution; implement pre-condition checks",
            "network_error": "Add retry with exponential backoff for network-dependent tasks",
            "resource_exhaustion": "Implement resource budgets and early termination thresholds",
            "rate_limited": "Add rate limiting awareness to scheduler; implement backoff queues",
        }
        return hints.get(
            pattern.failure_type,
            "Investigate root cause and add appropriate guardrails or validation"
        )
