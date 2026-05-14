"""
Evolution Engine — Unified orchestrator for controlled self-refactoring.

Coordinates the full evolution pipeline:
  1. Analyze: Detect drift, find optimizations, identify patterns
  2. Propose: Generate evolution proposals via PatchProposer
  3. Plan: Create ordered refactoring plan via RefactorPlanner
  4. Simulate: Test changes via MutationSimulator
  5. Benchmark: Validate performance impact
  6. Review: Package for human review

CRITICAL SAFETY RULES:
  - May PROPOSE, SIMULATE, BENCHMARK, COMPARE
  - May NOT self-deploy, auto-merge, bypass review, or mutate production runtime
  - All proposals require: governance approval, audit logging, rollback strategy
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from runtime.evolution_engine.patch_proposer import PatchProposer, PatchProposal
from runtime.evolution_engine.refactor_planner import RefactorPlanner, RefactorPlan
from runtime.evolution_engine.mutation_simulator import (
    MutationSimulator,
    SimulationResult,
    SystemTopology,
)
from runtime.evolution_engine.rollback_planner import RollbackPlanner, RollbackPlan
from runtime.evolution_engine.audit_logger import EvolutionAuditLogger

logger = logging.getLogger(__name__)


class EvolutionStatus(str, Enum):
    """Status of an evolution proposal through the pipeline."""
    ANALYZING = "analyzing"
    PROPOSING = "proposing"
    SIMULATING = "simulating"
    BENCHMARKING = "benchmarking"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


@dataclass
class BenchmarkResult:
    """Result of benchmarking a proposal."""
    benchmark_id: str = field(default_factory=lambda: f"bench_{uuid.uuid4().hex[:8]}")
    proposal_id: str = ""
    metrics_before: dict[str, Any] = field(default_factory=dict)
    metrics_after: dict[str, Any] = field(default_factory=dict)
    improvement_pct: float = 0.0
    regression_detected: bool = False
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "benchmark_id": self.benchmark_id,
            "proposal_id": self.proposal_id,
            "metrics_before": self.metrics_before,
            "metrics_after": self.metrics_after,
            "improvement_pct": round(self.improvement_pct, 2),
            "regression_detected": self.regression_detected,
            "details": self.details,
            "timestamp": self.timestamp,
        }


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment for an evolution proposal."""
    overall_risk: float = 0.0
    risk_factors: list[dict[str, Any]] = field(default_factory=list)
    mitigations: list[str] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "overall_risk": round(self.overall_risk, 4),
            "risk_factors": self.risk_factors,
            "mitigations": self.mitigations,
            "recommendation": self.recommendation,
        }


@dataclass
class EvolutionProposalPacket:
    """Complete evolution proposal package for review."""
    packet_id: str = field(default_factory=lambda: f"evo_{uuid.uuid4().hex[:12]}")
    proposals: list[PatchProposal] = field(default_factory=list)
    refactor_plan: RefactorPlan | None = None
    simulation_results: list[SimulationResult] = field(default_factory=list)
    rollback_plan: RollbackPlan | None = None
    benchmark: BenchmarkResult | None = None
    risk_assessment: RiskAssessment = field(default_factory=RiskAssessment)
    governance_requirements: list[str] = field(default_factory=list)
    status: EvolutionStatus = EvolutionStatus.ANALYZING
    created_at: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "packet_id": self.packet_id,
            "proposals": [p.to_dict() for p in self.proposals],
            "refactor_plan": self.refactor_plan.to_dict() if self.refactor_plan else None,
            "simulation_results": [s.to_dict() for s in self.simulation_results],
            "rollback_plan": self.rollback_plan.to_dict() if self.rollback_plan else None,
            "benchmark": self.benchmark.to_dict() if self.benchmark else None,
            "risk_assessment": self.risk_assessment.to_dict(),
            "governance_requirements": self.governance_requirements,
            "status": self.status.value,
            "created_at": self.created_at,
        }


class EvolutionEngine:
    """
    Unified evolution engine orchestrating the controlled self-refactoring pipeline.

    Coordinates analysis, proposal generation, planning, simulation,
    benchmarking, and review packaging. Never applies changes autonomously.

    SAFETY RULES:
      - May PROPOSE, SIMULATE, BENCHMARK, COMPARE
      - May NOT self-deploy, auto-merge, bypass review, mutate production runtime

    Usage:
        engine = EvolutionEngine()

        # Full pipeline
        packet = engine.propose()
        engine.simulate(packet)
        engine.benchmark(packet)
        review_doc = engine.create_review_packet(packet)

        # Or step-by-step
        analysis = engine.analyze()
        proposals = engine.propose()
    """

    def __init__(
        self,
        proposer: PatchProposer | None = None,
        planner: RefactorPlanner | None = None,
        simulator: MutationSimulator | None = None,
        rollback_planner: RollbackPlanner | None = None,
        audit_logger: EvolutionAuditLogger | None = None,
        topology: SystemTopology | None = None,
    ):
        self._proposer = proposer or PatchProposer()
        self._planner = planner or RefactorPlanner()
        self._simulator = simulator or MutationSimulator()
        self._rollback_planner = rollback_planner or RollbackPlanner()
        self._audit = audit_logger or EvolutionAuditLogger()
        self._topology = topology or SystemTopology()
        self._packets: list[EvolutionProposalPacket] = []

    def analyze(self) -> dict[str, Any]:
        """
        Perform full analysis: detect drift, find optimizations, identify patterns.

        Returns a summary of findings that can drive proposal generation.
        """
        logger.info("Evolution engine: starting analysis")
        start = time.time()

        analysis = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "topology": self._topology.to_dict(),
            "drift_indicators": self._detect_drift_indicators(),
            "optimization_opportunities": self._find_optimizations(),
            "patterns": self._identify_patterns(),
            "duration_ms": 0.0,
        }

        analysis["duration_ms"] = round((time.time() - start) * 1000, 2)
        logger.info("Analysis complete: %.1fms", analysis["duration_ms"])
        return analysis

    def propose(
        self,
        drift_reports: list[dict[str, Any]] | None = None,
        optimization_results: list[dict[str, Any]] | None = None,
        patterns: list[dict[str, Any]] | None = None,
    ) -> EvolutionProposalPacket:
        """
        Generate evolution proposals from analysis inputs.

        Creates a full proposal packet including:
          - Patch proposals
          - Refactoring plan
          - Rollback plan
          - Governance requirements

        Args:
            drift_reports: Detected drift to address
            optimization_results: Optimization opportunities
            patterns: Learned patterns to adapt to
        """
        logger.info("Evolution engine: generating proposals")

        all_proposals: list[PatchProposal] = []

        for drift in (drift_reports or []):
            proposals = self._proposer.propose_from_drift(drift)
            all_proposals.extend(proposals)

        for opt in (optimization_results or []):
            proposals = self._proposer.propose_from_optimization(opt)
            all_proposals.extend(proposals)

        if patterns:
            proposals = self._proposer.propose_from_patterns(patterns)
            all_proposals.extend(proposals)

        refactor_plan = self._planner.plan(all_proposals) if all_proposals else None
        rollback_plan = (
            self._rollback_planner.plan_rollback(refactor_plan)
            if refactor_plan else None
        )

        risk_assessment = self._assess_risk(all_proposals, refactor_plan)
        governance_reqs = self._determine_governance_requirements(
            all_proposals, risk_assessment
        )

        packet = EvolutionProposalPacket(
            proposals=all_proposals,
            refactor_plan=refactor_plan,
            rollback_plan=rollback_plan,
            risk_assessment=risk_assessment,
            governance_requirements=governance_reqs,
            status=EvolutionStatus.PROPOSING,
        )

        for proposal in all_proposals:
            self._audit.log_proposal(proposal)

        self._packets.append(packet)
        logger.info(
            "Proposals generated: %d patches, risk=%.2f",
            len(all_proposals), risk_assessment.overall_risk
        )
        return packet

    def simulate(self, proposal_packet: EvolutionProposalPacket) -> EvolutionProposalPacket:
        """
        Run simulation for a proposal packet.

        Applies proposed changes to a simulated copy of the topology
        and records the results.

        Args:
            proposal_packet: The proposal to simulate

        Returns:
            Updated packet with simulation results
        """
        logger.info("Evolution engine: simulating proposals")
        proposal_packet.status = EvolutionStatus.SIMULATING

        for proposal in proposal_packet.proposals:
            changes = self._proposal_to_changes(proposal)
            result = self._simulator.simulate(self._topology, changes)
            proposal_packet.simulation_results.append(result)
            self._audit.log_simulation(result)

        logger.info(
            "Simulation complete: %d results",
            len(proposal_packet.simulation_results)
        )
        return proposal_packet

    def benchmark(self, proposal_packet: EvolutionProposalPacket) -> EvolutionProposalPacket:
        """
        Benchmark a proposal packet to validate performance impact.

        Compares projected metrics before and after the proposed changes.

        Args:
            proposal_packet: The proposal to benchmark

        Returns:
            Updated packet with benchmark results
        """
        logger.info("Evolution engine: benchmarking proposals")
        proposal_packet.status = EvolutionStatus.BENCHMARKING

        metrics_before = self._collect_baseline_metrics()
        metrics_after = self._project_post_change_metrics(proposal_packet)

        improvement = self._calculate_improvement(metrics_before, metrics_after)
        regression = improvement < -1.0

        result = BenchmarkResult(
            proposal_id=proposal_packet.packet_id,
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            improvement_pct=improvement,
            regression_detected=regression,
            details={
                "proposal_count": len(proposal_packet.proposals),
                "simulation_count": len(proposal_packet.simulation_results),
            },
        )

        proposal_packet.benchmark = result
        proposal_packet.status = EvolutionStatus.AWAITING_REVIEW

        logger.info(
            "Benchmark complete: improvement=%.1f%%, regression=%s",
            improvement, regression
        )
        return proposal_packet

    def create_review_packet(self, proposal_packet: EvolutionProposalPacket) -> dict[str, Any]:
        """
        Create a formatted review document for human review.

        Includes: what changes, why, evidence, risks, rollback plan,
        benchmark results.

        Args:
            proposal_packet: The proposal packet to format

        Returns:
            Structured review document
        """
        review = {
            "packet_id": proposal_packet.packet_id,
            "status": proposal_packet.status.value,
            "created_at": proposal_packet.created_at,
            "summary": {
                "proposal_count": len(proposal_packet.proposals),
                "cumulative_risk": (
                    proposal_packet.refactor_plan.cumulative_risk
                    if proposal_packet.refactor_plan else 0.0
                ),
                "has_simulation": len(proposal_packet.simulation_results) > 0,
                "has_benchmark": proposal_packet.benchmark is not None,
                "has_rollback_plan": proposal_packet.rollback_plan is not None,
            },
            "proposals": [],
            "refactor_plan": (
                proposal_packet.refactor_plan.to_dict()
                if proposal_packet.refactor_plan else None
            ),
            "simulation_summary": self._summarize_simulations(
                proposal_packet.simulation_results
            ),
            "benchmark": (
                proposal_packet.benchmark.to_dict()
                if proposal_packet.benchmark else None
            ),
            "risk_assessment": proposal_packet.risk_assessment.to_dict(),
            "rollback_plan": (
                proposal_packet.rollback_plan.to_dict()
                if proposal_packet.rollback_plan else None
            ),
            "governance_requirements": proposal_packet.governance_requirements,
            "review_checklist": self._generate_review_checklist(proposal_packet),
        }

        for proposal in proposal_packet.proposals:
            review["proposals"].append({
                "patch_id": proposal.patch_id,
                "title": proposal.title,
                "type": proposal.type.value,
                "target_module": proposal.target_module,
                "description": proposal.description,
                "changes_description": proposal.changes_description,
                "risk_score": proposal.risk_score,
                "reversibility": proposal.reversibility,
            })

        return review

    def _detect_drift_indicators(self) -> list[dict[str, Any]]:
        """Detect drift indicators from current topology."""
        indicators: list[dict[str, Any]] = []

        for module, health in self._topology.health_scores.items():
            if health < 0.7:
                indicators.append({
                    "type": "health_degradation",
                    "module": module,
                    "health": health,
                    "threshold": 0.7,
                })

        return indicators

    def _find_optimizations(self) -> list[dict[str, Any]]:
        """Identify optimization opportunities."""
        opportunities: list[dict[str, Any]] = []

        for module, deps in self._topology.dependencies.items():
            if len(deps) > 4:
                opportunities.append({
                    "type": "high_coupling",
                    "module": module,
                    "dependency_count": len(deps),
                    "suggestion": "Consider introducing an abstraction layer",
                })

        return opportunities

    def _identify_patterns(self) -> list[dict[str, Any]]:
        """Identify recurring operational patterns."""
        return []

    def _assess_risk(
        self,
        proposals: list[PatchProposal],
        plan: RefactorPlan | None,
    ) -> RiskAssessment:
        """Assess overall risk of a set of proposals."""
        if not proposals:
            return RiskAssessment(recommendation="No proposals to assess")

        risk_factors: list[dict[str, Any]] = []
        max_risk = max(p.risk_score for p in proposals)
        avg_risk = sum(p.risk_score for p in proposals) / len(proposals)

        if max_risk > 0.7:
            risk_factors.append({
                "factor": "high_individual_risk",
                "description": f"At least one proposal has risk score {max_risk:.2f}",
                "severity": "high",
            })

        if plan and plan.conflicts:
            risk_factors.append({
                "factor": "conflicts_detected",
                "description": f"{len(plan.conflicts)} conflicts between patches",
                "severity": "medium",
            })

        if len(proposals) > 5:
            risk_factors.append({
                "factor": "batch_size",
                "description": f"Large batch of {len(proposals)} proposals",
                "severity": "medium",
            })

        overall = plan.cumulative_risk if plan else avg_risk

        mitigations = [
            "Apply patches incrementally with validation between steps",
            "Rollback plan prepared for each step",
            "Simulation validates no broken dependencies",
        ]

        if overall < 0.3:
            recommendation = "Low risk — safe to proceed with standard review"
        elif overall < 0.6:
            recommendation = "Moderate risk — recommend careful review and staged rollout"
        else:
            recommendation = "High risk — recommend splitting into smaller, safer batches"

        return RiskAssessment(
            overall_risk=overall,
            risk_factors=risk_factors,
            mitigations=mitigations,
            recommendation=recommendation,
        )

    def _determine_governance_requirements(
        self,
        proposals: list[PatchProposal],
        risk: RiskAssessment,
    ) -> list[str]:
        """Determine what governance approvals are needed."""
        requirements = [
            "Human review of proposal packet required",
            "Audit trail must be maintained",
            "Rollback plan must be validated before approval",
        ]

        if risk.overall_risk > 0.5:
            requirements.append("Senior review required due to elevated risk")

        if any(p.type.value == "evolve" for p in proposals):
            requirements.append("Evolution proposals require explicit architectural sign-off")

        return requirements

    def _proposal_to_changes(self, proposal: PatchProposal) -> list[dict[str, Any]]:
        """Convert a proposal to simulated change descriptors."""
        return [{
            "action": "modify_module",
            "module": proposal.target_module,
            "changes": {
                "proposed_patch": proposal.patch_id,
                "patch_type": proposal.type.value,
            },
        }]

    def _collect_baseline_metrics(self) -> dict[str, Any]:
        """Collect baseline metrics for benchmarking."""
        return {
            "module_count": len(self._topology.modules),
            "dependency_count": sum(len(v) for v in self._topology.dependencies.values()),
            "avg_health": (
                sum(self._topology.health_scores.values()) / len(self._topology.health_scores)
                if self._topology.health_scores else 0.0
            ),
        }

    def _project_post_change_metrics(
        self, packet: EvolutionProposalPacket
    ) -> dict[str, Any]:
        """Project metrics after proposed changes."""
        baseline = self._collect_baseline_metrics()

        projected_health_improvement = 0.0
        for sim in packet.simulation_results:
            projected_health_improvement += sim.health_score_delta

        return {
            "module_count": baseline["module_count"],
            "dependency_count": baseline["dependency_count"],
            "avg_health": baseline["avg_health"] + projected_health_improvement,
        }

    def _calculate_improvement(
        self, before: dict[str, Any], after: dict[str, Any]
    ) -> float:
        """Calculate percentage improvement between before/after metrics."""
        health_before = before.get("avg_health", 0.0)
        health_after = after.get("avg_health", 0.0)

        if health_before == 0:
            return 0.0

        return ((health_after - health_before) / health_before) * 100

    def _summarize_simulations(
        self, simulations: list[SimulationResult]
    ) -> dict[str, Any]:
        """Summarize simulation results."""
        if not simulations:
            return {"count": 0}

        total_broken = sum(len(s.broken_dependencies) for s in simulations)
        total_risks = sum(len(s.risk_areas) for s in simulations)
        avg_health_delta = (
            sum(s.health_score_delta for s in simulations) / len(simulations)
        )

        return {
            "count": len(simulations),
            "total_broken_dependencies": total_broken,
            "total_risk_areas": total_risks,
            "avg_health_score_delta": round(avg_health_delta, 4),
        }

    def _generate_review_checklist(
        self, packet: EvolutionProposalPacket
    ) -> list[dict[str, Any]]:
        """Generate a review checklist for the proposal packet."""
        checklist = [
            {
                "item": "All proposals reviewed individually",
                "required": True,
                "status": "pending",
            },
            {
                "item": "Simulation results validated",
                "required": True,
                "status": "done" if packet.simulation_results else "pending",
            },
            {
                "item": "Benchmark shows no regression",
                "required": True,
                "status": (
                    "done" if packet.benchmark and not packet.benchmark.regression_detected
                    else "pending"
                ),
            },
            {
                "item": "Rollback plan validated",
                "required": True,
                "status": "done" if packet.rollback_plan else "pending",
            },
            {
                "item": "Governance requirements satisfied",
                "required": True,
                "status": "pending",
            },
        ]
        return checklist
