"""Structured, prioritized refactor plan for decomposing IntegrationBus.

Produces a RefactorPlan with concrete, actionable steps organized by
priority (P0/P1/P2) and estimated effort. This is a PLAN, not execution.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from architecture.bus_decomposition.bus_risk_report import BusRiskReport
from architecture.bus_decomposition.event_schema import EventSchemaRegistry

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RefactorStep:
    id: str
    title: str
    description: str
    priority: str
    affected_files: list[str]
    risk: str
    reversible: bool
    dependencies: list[str]
    estimated_loc_change: int


@dataclass
class EffortEstimate:
    total_files: int = 0
    total_loc_change: int = 0
    estimated_phases: int = 0
    risk_summary: str = ""


@dataclass
class RefactorPlan:
    steps: list[RefactorStep] = field(default_factory=list)
    total_steps: int = 0
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    effort: EffortEstimate = field(default_factory=EffortEstimate)
    generated_at: str = ""


class RefactorPlanGenerator:
    """Generates a prioritized refactor plan for IntegrationBus decomposition."""

    def __init__(
        self,
        risk_report: BusRiskReport,
        schema_registry: EventSchemaRegistry,
    ) -> None:
        self._report = risk_report
        self._schemas = schema_registry

    def generate(self) -> RefactorPlan:
        steps: list[RefactorStep] = []
        steps.extend(self._plan_phase1_schemas())
        steps.extend(self._plan_phase2_unsubscribe())
        steps.extend(self._plan_phase3_replace_patches())
        steps.extend(self._plan_phase4_registry())
        steps.extend(self._plan_phase5_async())

        p0 = [s for s in steps if s.priority == "P0"]
        p1 = [s for s in steps if s.priority == "P1"]
        p2 = [s for s in steps if s.priority == "P2"]
        effort = self._estimate_effort(steps)

        return RefactorPlan(
            steps=steps,
            total_steps=len(steps),
            p0_count=len(p0),
            p1_count=len(p1),
            p2_count=len(p2),
            effort=effort,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _plan_phase1_schemas(self) -> list[RefactorStep]:
        return [
            RefactorStep(
                id="P1-01",
                title="Define typed event schemas for all 29 connections",
                description=(
                    "Create BusEventSchema dataclasses for every IntegrationBus "
                    "connection, documenting source, target, mechanism, and payload "
                    "fields. This replaces implicit coupling with explicit contracts. "
                    "(Completed in this phase — architecture/bus_decomposition/event_schema.py)"
                ),
                priority="P0",
                affected_files=["architecture/bus_decomposition/event_schema.py"],
                risk="low",
                reversible=True,
                dependencies=[],
                estimated_loc_change=400,
            ),
            RefactorStep(
                id="P1-02",
                title="Add event validation to IntegrationBus._log_event",
                description=(
                    "Before logging a bus event, validate it against the schema "
                    "registry. Log warnings for unknown connections or missing fields. "
                    "This catches wiring errors at runtime without blocking dispatch."
                ),
                priority="P0",
                affected_files=[
                    "kernel/integration_bus.py",
                    "architecture/bus_decomposition/event_schema.py",
                ],
                risk="low",
                reversible=True,
                dependencies=["P1-01"],
                estimated_loc_change=30,
            ),
        ]

    def _plan_phase2_unsubscribe(self) -> list[RefactorStep]:
        return [
            RefactorStep(
                id="P2-01",
                title="Add return-unsubscribe to Scheduler.on_event()",
                description=(
                    "Modify Scheduler.on_event to return a callable that removes "
                    "the registered callback. This enables IntegrationBus.unwire() "
                    "to cleanly remove 5 scheduler subscriptions (tasks_to_tracer, "
                    "failure_propagation, checkpoint_cleanup, execution_to_patterns, "
                    "optimizer_to_scheduler)."
                ),
                priority="P0",
                affected_files=["runtime/task_graph/scheduler.py"],
                risk="low",
                reversible=True,
                dependencies=[],
                estimated_loc_change=15,
            ),
            RefactorStep(
                id="P2-02",
                title="Add return-unsubscribe to AttentionManager.on_change()",
                description=(
                    "Modify AttentionManager.on_change to return a callable that "
                    "removes the callback. Covers somatic_to_scheduler, somatic_to_context, "
                    "attention_to_governance, and attention_to_agents."
                ),
                priority="P0",
                affected_files=["somatic/attention_manager.py"],
                risk="low",
                reversible=True,
                dependencies=[],
                estimated_loc_change=15,
            ),
            RefactorStep(
                id="P2-03",
                title="Add return-unsubscribe to InjectionLogger.on_injection()",
                description=(
                    "Modify InjectionLogger.on_injection to return a callable "
                    "that removes the callback. Covers injection_to_tracer and "
                    "context_costs."
                ),
                priority="P0",
                affected_files=["context/injection_logger.py"],
                risk="low",
                reversible=True,
                dependencies=[],
                estimated_loc_change=10,
            ),
            RefactorStep(
                id="P2-04",
                title="Add return-unsubscribe to SignalCorrelator.on_correlation()",
                description=(
                    "Modify SignalCorrelator.on_correlation to return a callable "
                    "that removes the callback. Covers signal_correlator connection."
                ),
                priority="P0",
                affected_files=["somatic/signal_correlator.py"],
                risk="low",
                reversible=True,
                dependencies=[],
                estimated_loc_change=10,
            ),
            RefactorStep(
                id="P2-05",
                title="Add return-unsubscribe to SomaticSignalBus.on_signal()",
                description=(
                    "Modify SomaticSignalBus.on_signal/subscribe to return a "
                    "callable that removes the callback. Covers attention_runtime."
                ),
                priority="P0",
                affected_files=["somatic/signal_bus.py"],
                risk="low",
                reversible=True,
                dependencies=[],
                estimated_loc_change=10,
            ),
            RefactorStep(
                id="P2-06",
                title="Store unsubscribe handles in IntegrationBus",
                description=(
                    "Update IntegrationBus.wire() and wire_v03() to store all "
                    "unsubscribe handles returned by the new APIs. Update unwire() "
                    "and unwire_v03() to call each handle on disconnect."
                ),
                priority="P0",
                affected_files=["kernel/integration_bus.py"],
                risk="medium",
                reversible=True,
                dependencies=["P2-01", "P2-02", "P2-03", "P2-04", "P2-05"],
                estimated_loc_change=60,
            ),
        ]

    def _plan_phase3_replace_patches(self) -> list[RefactorStep]:
        return [
            RefactorStep(
                id="P3-01",
                title="Replace gate.check monkey-patch chain with pre/post hooks",
                description=(
                    "Add a HookableMixin or pre_check/post_check hook lists to "
                    "MandatoryGate. Each of the 4 current monkey-patches "
                    "(mandatory_gate_audit, tool_permission_somatic, "
                    "incidents_to_learner, cognition_tracing) becomes an "
                    "independent post_check subscriber. This eliminates the "
                    "fragile 4-deep stacking."
                ),
                priority="P1",
                affected_files=[
                    "governance/mandatory_gate.py",
                    "kernel/integration_bus.py",
                ],
                risk="high",
                reversible=True,
                dependencies=["P2-06"],
                estimated_loc_change=120,
            ),
            RefactorStep(
                id="P3-02",
                title="Replace memory.recall/store monkey-patches with pre/post hooks",
                description=(
                    "Add pre_recall/post_recall and pre_store/post_store hook "
                    "lists to MemoryKernel. memory_metrics and memory_flow "
                    "become independent post_recall subscribers."
                ),
                priority="P1",
                affected_files=[
                    "memory/memory_kernel.py",
                    "kernel/integration_bus.py",
                ],
                risk="medium",
                reversible=True,
                dependencies=["P2-06"],
                estimated_loc_change=80,
            ),
            RefactorStep(
                id="P3-03",
                title="Replace validator.validate monkey-patch with post-validation hook",
                description=(
                    "Add a post_validate hook list to PolicyValidator. "
                    "governance_to_audit becomes a subscriber instead of a "
                    "method wrapper."
                ),
                priority="P1",
                affected_files=[
                    "governance/policy_engine.py",
                    "kernel/integration_bus.py",
                ],
                risk="medium",
                reversible=True,
                dependencies=["P2-06"],
                estimated_loc_change=50,
            ),
            RefactorStep(
                id="P3-04",
                title="Replace kernel.health monkey-patch with health extension registry",
                description=(
                    "Add a register_health_extension API to AmbientKernel that "
                    "merges additional health data into the health() response. "
                    "analytics_to_health becomes a registered extension."
                ),
                priority="P1",
                affected_files=[
                    "kernel/__init__.py",
                    "kernel/integration_bus.py",
                ],
                risk="low",
                reversible=True,
                dependencies=[],
                estimated_loc_change=40,
            ),
            RefactorStep(
                id="P3-05",
                title="Replace telemetry.complete_task monkey-patch with post-completion hook",
                description=(
                    "Add a post_complete hook to telemetry. agent_decision_log "
                    "becomes a subscriber instead of a wrapper."
                ),
                priority="P1",
                affected_files=[
                    "observability/telemetry.py",
                    "kernel/integration_bus.py",
                ],
                risk="low",
                reversible=True,
                dependencies=[],
                estimated_loc_change=40,
            ),
            RefactorStep(
                id="P3-06",
                title="Replace remaining v0.3 monkey-patches with hooks",
                description=(
                    "Convert self_model.snapshot, drift_detector.detect, "
                    "budget_manager.allocate, throttle.update, "
                    "reporter.generate_report, and proposer.propose_from_patterns "
                    "from monkey-patches to hook-based subscriptions."
                ),
                priority="P1",
                affected_files=[
                    "identity/cognitive_self_model.py",
                    "observability/drift_detector.py",
                    "context/budget_manager.py",
                    "somatic/attention_runtime.py",
                    "memory/evolution/efficiency_reporter.py",
                    "memory/evolution/optimization_proposer.py",
                    "kernel/integration_bus.py",
                ],
                risk="high",
                reversible=True,
                dependencies=["P3-01", "P3-02"],
                estimated_loc_change=200,
            ),
        ]

    def _plan_phase4_registry(self) -> list[RefactorStep]:
        return [
            RefactorStep(
                id="P4-01",
                title="Integrate ConnectionRegistry into IntegrationBus.wire()",
                description=(
                    "Update IntegrationBus to use ConnectionRegistry for tracking "
                    "wire/unwire state. Each _wire_*() method calls "
                    "registry.register_connection() and each cleanup calls "
                    "registry.unregister_connection()."
                ),
                priority="P1",
                affected_files=[
                    "kernel/integration_bus.py",
                    "architecture/bus_decomposition/connection_registry.py",
                ],
                risk="medium",
                reversible=True,
                dependencies=["P2-06"],
                estimated_loc_change=80,
            ),
            RefactorStep(
                id="P4-02",
                title="Add connection health to IntegrationBus.status()",
                description=(
                    "Extend IntegrationBus.status() to include "
                    "ConnectionRegistry.check_health() and dependency_matrix. "
                    "This provides runtime visibility into bus health."
                ),
                priority="P1",
                affected_files=["kernel/integration_bus.py"],
                risk="low",
                reversible=True,
                dependencies=["P4-01"],
                estimated_loc_change=20,
            ),
            RefactorStep(
                id="P4-03",
                title="Resolve double-auditing: MandatoryGate vs governance_to_audit",
                description=(
                    "Decide on a single audit path. Recommended: remove the "
                    "governance_to_audit bus connection and let MandatoryGate "
                    "own its own audit logging. Document the decision."
                ),
                priority="P1",
                affected_files=[
                    "kernel/integration_bus.py",
                    "governance/mandatory_gate.py",
                ],
                risk="medium",
                reversible=True,
                dependencies=["P3-01"],
                estimated_loc_change=30,
            ),
            RefactorStep(
                id="P4-04",
                title="Unify scheduler concurrency control",
                description=(
                    "Replace the competing writes from somatic_to_scheduler and "
                    "throttle_to_scheduler with a single ConcurrencyPolicy that "
                    "combines attention state and throttle state."
                ),
                priority="P1",
                affected_files=[
                    "kernel/integration_bus.py",
                    "runtime/task_graph/scheduler.py",
                ],
                risk="medium",
                reversible=True,
                dependencies=["P3-01"],
                estimated_loc_change=60,
            ),
        ]

    def _plan_phase5_async(self) -> list[RefactorStep]:
        return [
            RefactorStep(
                id="P5-01",
                title="Add async dispatch option to SomaticSignalBus",
                description=(
                    "Allow SomaticSignalBus handlers to be dispatched "
                    "asynchronously via asyncio.create_task with configurable "
                    "timeouts. This prevents slow handlers from blocking signal "
                    "dispatch."
                ),
                priority="P2",
                affected_files=["somatic/signal_bus.py"],
                risk="medium",
                reversible=True,
                dependencies=["P2-05"],
                estimated_loc_change=50,
            ),
            RefactorStep(
                id="P5-02",
                title="Add cascade depth tracking and circuit breaker",
                description=(
                    "Track dispatch depth in _log_event and all callback chains. "
                    "If depth exceeds a configurable threshold, log a warning and "
                    "optionally break the cascade."
                ),
                priority="P2",
                affected_files=[
                    "kernel/integration_bus.py",
                    "somatic/signal_bus.py",
                ],
                risk="medium",
                reversible=True,
                dependencies=["P4-01"],
                estimated_loc_change=60,
            ),
            RefactorStep(
                id="P5-03",
                title="Replace kernel reference with narrow BusContext interface",
                description=(
                    "Define a BusContext dataclass or protocol that exposes only "
                    "the subsystem references IntegrationBus needs. This decouples "
                    "the bus from the kernel's internal structure."
                ),
                priority="P2",
                affected_files=[
                    "kernel/integration_bus.py",
                    "kernel/__init__.py",
                ],
                risk="high",
                reversible=True,
                dependencies=["P3-06"],
                estimated_loc_change=100,
            ),
            RefactorStep(
                id="P5-04",
                title="Add persistent event log with dropped-event counter",
                description=(
                    "Replace the in-memory 500-entry capped event_log with a "
                    "ring buffer that tracks total events, dropped count, and "
                    "can optionally flush to a persistent JSONL file."
                ),
                priority="P2",
                affected_files=["kernel/integration_bus.py"],
                risk="low",
                reversible=True,
                dependencies=[],
                estimated_loc_change=40,
            ),
            RefactorStep(
                id="P5-05",
                title="Consolidate duplicate constants into shared config module",
                description=(
                    "Several hardcoded values appear across bus connections: "
                    "pressure thresholds (40.0, 50.0, 80.0), log truncation "
                    "lengths (40, 100, 200, 300), checkpoint retention count (5), "
                    "health window (300s). Move these to a shared configuration."
                ),
                priority="P2",
                affected_files=[
                    "kernel/integration_bus.py",
                    "kernel/bus_config.py",
                ],
                risk="low",
                reversible=True,
                dependencies=[],
                estimated_loc_change=50,
            ),
        ]

    def _estimate_effort(self, steps: list[RefactorStep]) -> EffortEstimate:
        all_files: set[str] = set()
        total_loc = 0
        for step in steps:
            all_files.update(step.affected_files)
            total_loc += step.estimated_loc_change

        critical_or_high = sum(
            1 for f in self._report.findings
            if f.severity in ("critical", "high")
        )

        return EffortEstimate(
            total_files=len(all_files),
            total_loc_change=total_loc,
            estimated_phases=5,
            risk_summary=(
                f"{critical_or_high} critical/high findings drive P0/P1 priorities. "
                f"gate.check 4-deep stacking is the highest-risk item. "
                f"Callback unsubscribe support is the broadest prerequisite."
            ),
        )
