"""
Skillify Agent — Automated skill discovery and governance-gated registration.

Observes workflow executions, mines recurring patterns, clusters them,
generates candidate skill definitions, validates them, and proposes them
through a governance-gated registration pipeline.

Key principle: Skillify may only PROPOSE candidate skills. All candidates
require explicit governance approval before registration, and all
registrations are reversible.

Usage:
    from agents.skillify import generate_sample_candidate
    candidate = generate_sample_candidate()
"""

from __future__ import annotations

from agents.skillify.workflow_observer import (
    WorkflowEvent,
    WorkflowStep,
    WorkflowObserver,
)
from agents.skillify.pattern_miner import (
    WorkflowPattern,
    SkillifyPatternMiner,
)
from agents.skillify.workflow_cluster import (
    WorkflowClusterGroup,
    WorkflowCluster,
)
from agents.skillify.skill_candidate_generator import (
    SkillCandidate,
    SkillCandidateGenerator,
)
from agents.skillify.skill_candidate_validator import (
    CandidateValidation,
    SimulationResult,
    SkillCandidateValidator,
)
from agents.skillify.skill_registration_pipeline import (
    ProposalResult,
    ApprovalResult,
    RegistrationResult,
    SkillRegistrationPipeline,
)


def generate_sample_candidate() -> SkillCandidate:
    """
    End-to-end demo: create synthetic workflow events for an
    "anomaly_detection" pattern, run them through the full
    observe → mine → cluster → generate → validate pipeline,
    and return the resulting SkillCandidate (status="draft").

    The candidate is NOT auto-registered — it must go through
    governance approval via SkillRegistrationPipeline.
    """
    import uuid
    from datetime import datetime, timedelta, timezone

    base_time = datetime.now(timezone.utc) - timedelta(hours=2)

    observer = WorkflowObserver.__new__(WorkflowObserver)
    observer._storage_path = None  # type: ignore[assignment]
    observer._events = []

    events: list[WorkflowEvent] = []
    for i in range(8):
        ts = base_time + timedelta(minutes=i * 10)
        success = i != 3  # one failure for realism
        duration = 450.0 + (i * 20) + (0 if success else 200)

        steps = [
            WorkflowStep(
                step_name="detect_anomaly",
                module="agents.specialists",
                function="run_anomaly_detection",
                duration_ms=duration * 0.4,
                success=True,
            ),
            WorkflowStep(
                step_name="explain_anomaly",
                module="agents.specialists",
                function="generate_explanation",
                duration_ms=duration * 0.35,
                success=success,
            ),
            WorkflowStep(
                step_name="log_finding",
                module="governance.audit_log",
                function="record_decision",
                duration_ms=duration * 0.25,
                success=True,
            ),
        ]

        event = WorkflowEvent(
            event_id=str(uuid.uuid4()),
            timestamp=ts,
            workflow_type="anomaly_detection",
            steps=steps,
            inputs={
                "metric_name": f"cpu_usage_{i % 3}",
                "threshold": 0.85,
                "window_minutes": 15,
            },
            outputs={
                "anomaly_detected": True,
                "severity": "medium" if i % 2 == 0 else "high",
                "explanation": f"Synthetic anomaly explanation #{i}",
            },
            success=success,
            duration_ms=duration,
            agent_id="monitoring-agent",
            governance_checks=["policy_engine.evaluate"],
        )
        events.append(event)
        observer._events.append(event)

    miner = SkillifyPatternMiner()
    patterns = miner.mine(events, min_support=3)

    clusterer = WorkflowCluster()
    clusters = clusterer.cluster(patterns, threshold=0.5)

    if not clusters:
        from agents.skillify.skill_candidate_generator import SkillCandidate
        from datetime import datetime, timezone
        return SkillCandidate(
            candidate_id=str(uuid.uuid4()),
            proposed_name="auto_anomaly_detection",
            proposed_version="0.1.0",
            description="Fallback candidate — no clusters produced",
            proposed_inputs=[{"name": "metric_name", "type": "str", "required": True}],
            proposed_outputs=[{"name": "anomaly_detected", "type": "bool"}],
            confidence_range=(0.7, 0.9),
            routing_conditions=["workflow_type == 'anomaly_detection'"],
            memory_updates=["record_execution_result"],
            governance_level="REVIEW_REQUIRED",
            observability_hooks=["emit_start_event", "emit_completion_event"],
            source_patterns=[],
            evidence={"occurrence_count": len(events), "success_rate": 0.875},
            status="draft",
            created_at=datetime.now(timezone.utc),
        )

    generator = SkillCandidateGenerator.__new__(SkillCandidateGenerator)
    generator._candidates_path = None  # type: ignore[assignment]
    # Override _persist to avoid disk writes in demo mode
    generator._persist = lambda candidate: None  # type: ignore[assignment]
    candidate = generator.generate(clusters[0])

    validator = SkillCandidateValidator()
    validation = validator.validate(candidate)

    candidate.status = "draft"

    return candidate


__all__ = [
    # workflow_observer
    "WorkflowEvent",
    "WorkflowStep",
    "WorkflowObserver",
    # pattern_miner
    "WorkflowPattern",
    "SkillifyPatternMiner",
    # workflow_cluster
    "WorkflowClusterGroup",
    "WorkflowCluster",
    # skill_candidate_generator
    "SkillCandidate",
    "SkillCandidateGenerator",
    # skill_candidate_validator
    "CandidateValidation",
    "SimulationResult",
    "SkillCandidateValidator",
    # skill_registration_pipeline
    "ProposalResult",
    "ApprovalResult",
    "RegistrationResult",
    "SkillRegistrationPipeline",
    # demo
    "generate_sample_candidate",
]
