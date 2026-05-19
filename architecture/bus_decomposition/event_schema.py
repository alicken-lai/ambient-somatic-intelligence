"""Typed event contracts for all 29 IntegrationBus connections.

Replaces implicit coupling with explicit, documented contracts.
Each connection has a BusEventSchema describing its source, target,
mechanism, and the exact payload fields that flow through it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EventField:
    name: str
    type_hint: str
    required: bool
    description: str


@dataclass(frozen=True)
class BusEventSchema:
    name: str
    source_subsystem: str
    target_subsystem: str
    payload_type: str
    description: str
    mechanism: str
    version: str
    is_bidirectional: bool
    payload_fields: list[EventField]


@dataclass
class EventValidationResult:
    valid: bool
    connection_name: str
    errors: list[str] = field(default_factory=list)


def _build_v02_schemas() -> list[BusEventSchema]:
    return [
        BusEventSchema(
            name="somatic_to_scheduler",
            source_subsystem="somatic.attention",
            target_subsystem="task_graph.scheduler",
            payload_type="AttentionStateChange",
            description=(
                "When attention level changes, adjust scheduler concurrency. "
                "Reads new_max_concurrency from AttentionState and writes it to "
                "scheduler.config.max_concurrent."
            ),
            mechanism="callback",
            version="v0.2",
            is_bidirectional=False,
            payload_fields=[
                EventField("old_level", "str", True, "Previous attention level label"),
                EventField("new_level", "str", True, "New attention level label"),
                EventField("new_max_concurrency", "int", True, "Target max_concurrent value for scheduler"),
            ],
        ),
        BusEventSchema(
            name="somatic_to_context",
            source_subsystem="somatic.attention",
            target_subsystem="context.budget_manager",
            payload_type="AttentionBudgetAdjustment",
            description=(
                "When system is stressed, reduce context token budgets. "
                "Reads context_budget_ratio from AttentionState and scales "
                "BudgetManager.total_budget accordingly."
            ),
            mechanism="callback",
            version="v0.2",
            is_bidirectional=False,
            payload_fields=[
                EventField("old_level", "str", True, "Previous attention level label"),
                EventField("new_level", "str", True, "New attention level label"),
                EventField("ratio", "float", True, "Budget scaling ratio from AttentionState"),
                EventField("original_budget", "int", True, "Original total_budget before scaling"),
                EventField("new_budget", "int", True, "Scaled total_budget"),
            ],
        ),
        BusEventSchema(
            name="attention_to_governance",
            source_subsystem="somatic.attention",
            target_subsystem="governance",
            payload_type="GovernanceSensitivityChange",
            description=(
                "When attention rises, log governance sensitivity change. "
                "Only fires when new governance_sensitivity exceeds the old value."
            ),
            mechanism="callback",
            version="v0.2",
            is_bidirectional=False,
            payload_fields=[
                EventField("old_sensitivity", "float", True, "Previous governance_sensitivity multiplier"),
                EventField("new_sensitivity", "float", True, "New governance_sensitivity multiplier"),
            ],
        ),
        BusEventSchema(
            name="governance_to_audit",
            source_subsystem="governance.validator",
            target_subsystem="governance.audit_log",
            payload_type="ValidationDecisionRecord",
            description=(
                "Auto-record every validation decision into the audit log. "
                "Monkey-patches validator.validate to call audit_log.record_decision "
                "after each validation."
            ),
            mechanism="monkey_patch",
            version="v0.2",
            is_bidirectional=False,
            payload_fields=[
                EventField("action", "str", True, "The action string that was validated"),
                EventField("risk", "str", True, "RiskLevel name from validation result"),
                EventField("reason", "str", True, "Blocking stage details or 'Allowed'"),
                EventField("agent_id", "str", True, "ID of the agent requesting validation"),
                EventField("matched_policies", "list[str]", True, "Policy names matched during validation"),
                EventField("validation_stages", "list[dict]", True, "Stage results: name, passed, risk"),
            ],
        ),
        BusEventSchema(
            name="tasks_to_tracer",
            source_subsystem="task_graph.scheduler",
            target_subsystem="observability.tracer",
            payload_type="SchedulerEventTrace",
            description=(
                "Auto-trace scheduler events into the observability layer. "
                "Subscribes to Scheduler.on_event and calls tracer.record_event."
            ),
            mechanism="callback",
            version="v0.2",
            is_bidirectional=False,
            payload_fields=[
                EventField("event_name", "str", True, "Scheduler event value (e.g. 'task_started')"),
                EventField("task_id", "str", False, "Task ID from event data, if present"),
                EventField("attributes", "dict", True, "Full event data dict forwarded to tracer"),
            ],
        ),
        BusEventSchema(
            name="attention_to_agents",
            source_subsystem="somatic.attention",
            target_subsystem="agent_runtime",
            payload_type="AgentParallelismAdjustment",
            description=(
                "Adjust agent parallelism preferences when system is stressed. "
                "Caps each agent's parallelism to new max_concurrency. "
                "Also logs pause recommendation when overwhelmed."
            ),
            mechanism="callback",
            version="v0.2",
            is_bidirectional=False,
            payload_fields=[
                EventField("old_level", "str", True, "Previous attention level label"),
                EventField("new_level", "str", True, "New attention level label"),
                EventField("max_concurrency", "int", True, "New parallelism cap for all agents"),
                EventField("should_pause_non_critical", "bool", True, "Whether non-critical agents should pause"),
            ],
        ),
        BusEventSchema(
            name="memory_metrics",
            source_subsystem="memory.kernel",
            target_subsystem="observability.metrics",
            payload_type="MemoryRecallMetrics",
            description=(
                "Track memory recall operations in observability metrics. "
                "Monkey-patches memory.recall to call metrics.increment after each recall."
            ),
            mechanism="monkey_patch",
            version="v0.2",
            is_bidirectional=False,
            payload_fields=[
                EventField("query", "str", True, "Recall query string (truncated to 40 chars in log)"),
                EventField("results_count", "int", True, "Number of records returned"),
                EventField("total_tokens", "int", True, "Total tokens in recall result"),
                EventField("dedup_removed", "int", True, "Count of deduplicated records removed"),
            ],
        ),
        BusEventSchema(
            name="injection_to_tracer",
            source_subsystem="context.injection_logger",
            target_subsystem="observability.tracer",
            payload_type="ContextInjectionTrace",
            description=(
                "Auto-trace context injection events into the observability layer. "
                "Subscribes to InjectionLogger.on_injection and records in both "
                "tracer and metrics."
            ),
            mechanism="callback",
            version="v0.2",
            is_bidirectional=False,
            payload_fields=[
                EventField("agent_id", "str", True, "Agent receiving the injection"),
                EventField("query", "str", True, "Context query (truncated to 100 chars)"),
                EventField("memory_count", "int", True, "Number of memories injected"),
                EventField("tokens_used", "int", True, "Tokens consumed by injection"),
                EventField("layers_used", "int", True, "Number of memory layers queried"),
                EventField("top_score", "float", True, "Highest relevance score (rounded to 4 decimals)"),
                EventField("compression_applied", "bool", True, "Whether compression was used"),
            ],
        ),
        BusEventSchema(
            name="failure_propagation",
            source_subsystem="task_graph.scheduler",
            target_subsystem="task_graph.failure_propagator",
            payload_type="FailurePropagationResult",
            description=(
                "Auto-propagate failures through the DAG. On TASK_FAILED, "
                "FailurePropagator marks downstream dependents as SKIPPED "
                "and the bus relays this to the tracer."
            ),
            mechanism="callback",
            version="v0.2",
            is_bidirectional=False,
            payload_fields=[
                EventField("task_id", "str", True, "Root task that failed"),
                EventField("skipped_count", "int", True, "Number of downstream tasks skipped"),
                EventField("affected_task_ids", "list[str]", True, "IDs of all skipped downstream tasks"),
            ],
        ),
        BusEventSchema(
            name="checkpoint_cleanup",
            source_subsystem="task_graph.scheduler",
            target_subsystem="task_graph.checkpoint",
            payload_type="CheckpointCleanupResult",
            description=(
                "Run checkpoint cleanup after each graph completion. "
                "Triggers on GRAPH_COMPLETED or GRAPH_FAILED, calls "
                "checkpoint.cleanup_all_graphs(keep_latest_n=5)."
            ),
            mechanism="callback",
            version="v0.2",
            is_bidirectional=False,
            payload_fields=[
                EventField("event_type", "str", True, "GRAPH_COMPLETED or GRAPH_FAILED"),
                EventField("removed_count", "int", True, "Number of old checkpoint files removed"),
                EventField("keep_latest_n", "int", True, "Retention count (hardcoded to 5)"),
            ],
        ),
        BusEventSchema(
            name="mandatory_gate_audit",
            source_subsystem="governance.mandatory_gate",
            target_subsystem="observability.tracer",
            payload_type="GateCheckTrace",
            description=(
                "Ensure all MandatoryGate checks are traced in observability. "
                "Monkey-patches gate.check to call tracer.record_event. "
                "This is the first layer in the gate.check patch chain."
            ),
            mechanism="monkey_patch",
            version="v0.2",
            is_bidirectional=False,
            payload_fields=[
                EventField("action", "str", True, "Action checked (truncated to 100 chars)"),
                EventField("agent_id", "str", True, "Agent requesting the check"),
                EventField("allowed", "bool", True, "Whether the gate allowed the action"),
                EventField("risk_level", "str", True, "RiskLevel name from gate result"),
                EventField("reason", "str", True, "Gate decision reason (truncated to 200 chars)"),
            ],
        ),
        BusEventSchema(
            name="tool_permission_somatic",
            source_subsystem="governance.tool_permissions",
            target_subsystem="somatic.bus",
            payload_type="ToolPermissionDenialSignal",
            description=(
                "Emit somatic pain signal when tool permissions are denied. "
                "Monkey-patches gate.check (stacks on mandatory_gate_audit). "
                "Only fires when permission_result.is_denied is True."
            ),
            mechanism="monkey_patch",
            version="v0.2",
            is_bidirectional=False,
            payload_fields=[
                EventField("agent_id", "str", True, "Agent whose permission was denied"),
                EventField("tool_name", "str", True, "Name of the denied tool"),
                EventField("is_denied", "bool", True, "Always True when this fires"),
                EventField("pressure_value", "float", True, "Pressure signal value (hardcoded 80.0)"),
                EventField("pressure_threshold", "float", True, "Threshold for triggering (hardcoded 50.0)"),
            ],
        ),
        BusEventSchema(
            name="signal_correlator",
            source_subsystem="somatic.correlator",
            target_subsystem="observability.tracer",
            payload_type="CorrelationEvent",
            description=(
                "Activate the signal correlator to detect compound patterns. "
                "Subscribes via correlator.on_correlation and forwards "
                "the event to the tracer."
            ),
            mechanism="callback",
            version="v0.2",
            is_bidirectional=False,
            payload_fields=[
                EventField("rule_name", "str", True, "Name of the correlation rule that matched"),
                EventField("matched_signals_count", "int", True, "Number of signals in the pattern"),
                EventField("severity_multiplier", "float", True, "Severity multiplier from correlation"),
            ],
        ),
        BusEventSchema(
            name="rate_tracker",
            source_subsystem="somatic.bus",
            target_subsystem="somatic.rate_tracker",
            payload_type="SubscriptionOnly",
            description=(
                "Activate the rate tracker to monitor signal rates and spike detection. "
                "Calls tracker.subscribe() — no per-event payload; the tracker "
                "internally subscribes to the somatic bus."
            ),
            mechanism="callback",
            version="v0.2",
            is_bidirectional=False,
            payload_fields=[],
        ),
        BusEventSchema(
            name="analytics_to_health",
            source_subsystem="somatic.analytics",
            target_subsystem="kernel.health",
            payload_type="SomaticHealthReport",
            description=(
                "Wire analytics into the kernel health reporting. "
                "Monkey-patches kernel.health() to merge a somatic_health "
                "report (window_seconds=300) into the health dict."
            ),
            mechanism="monkey_patch",
            version="v0.2",
            is_bidirectional=False,
            payload_fields=[
                EventField("window_seconds", "int", True, "Health report window (hardcoded 300)"),
                EventField("health_score", "float", True, "Somatic health score from analytics"),
                EventField("report_dict", "dict", True, "Full health report as dict via to_dict()"),
            ],
        ),
        BusEventSchema(
            name="agent_decision_log",
            source_subsystem="observability.telemetry",
            target_subsystem="observability.decision_log",
            payload_type="AgentTaskDecision",
            description=(
                "Auto-record agent task completions as decision events. "
                "Monkey-patches telemetry.complete_task to call "
                "decision_log.log_decision after each completion."
            ),
            mechanism="monkey_patch",
            version="v0.2",
            is_bidirectional=False,
            payload_fields=[
                EventField("agent_id", "str", True, "Agent that completed the task"),
                EventField("task_id", "str", True, "Task identifier"),
                EventField("success", "bool", True, "Whether the task succeeded"),
                EventField("task_name", "str", True, "Human-readable task name from result"),
                EventField("status", "str", True, "Final task status"),
                EventField("duration_ms", "int", True, "Task duration in milliseconds"),
                EventField("tokens_used", "int", True, "Tokens consumed by the task"),
                EventField("confidence", "float", True, "1.0 if success else 0.0"),
                EventField("strategy_chosen", "str", True, "Always 'task_execution'"),
                EventField("governance_result", "str", True, "Always 'ALLOW'"),
            ],
        ),
    ]


def _build_v03_schemas() -> list[BusEventSchema]:
    return [
        BusEventSchema(
            name="self_model_drift",
            source_subsystem="identity.self_model",
            target_subsystem="observability.drift_detector",
            payload_type="DriftDetectionTrigger",
            description=(
                "When CognitiveSelfModel builds a snapshot, trigger "
                "DriftDetector.detect(). Monkey-patches self_model.snapshot."
            ),
            mechanism="monkey_patch",
            version="v0.3",
            is_bidirectional=False,
            payload_fields=[
                EventField("overall_risk_score", "float", True, "Drift risk score from detection"),
                EventField("remediation_proposals_count", "int", True, "Number of remediation proposals generated"),
            ],
        ),
        BusEventSchema(
            name="drift_to_somatic",
            source_subsystem="observability.drift_detector",
            target_subsystem="somatic.bus",
            payload_type="DriftPressureSignal",
            description=(
                "When drift finds HIGH/CRITICAL issues, emit PRESSURE on "
                "SignalBus. Monkey-patches drift_detector.detect."
            ),
            mechanism="monkey_patch",
            version="v0.3",
            is_bidirectional=False,
            payload_fields=[
                EventField("high_critical_count", "int", True, "Number of HIGH/CRITICAL remediation proposals"),
                EventField("overall_risk_score", "float", True, "Overall drift risk score"),
                EventField("pressure_value", "float", True, "min(100.0, overall_risk_score)"),
                EventField("pressure_threshold", "float", True, "Threshold for triggering (hardcoded 40.0)"),
            ],
        ),
        BusEventSchema(
            name="execution_to_patterns",
            source_subsystem="task_graph.scheduler",
            target_subsystem="memory.evolution.pattern_miner",
            payload_type="PatternMiningTrigger",
            description=(
                "After GRAPH_COMPLETED, trigger PatternMiner to record the "
                "execution. Subscribes to Scheduler.on_event."
            ),
            mechanism="callback",
            version="v0.3",
            is_bidirectional=False,
            payload_fields=[
                EventField("graph_id", "str", False, "Graph ID from event data"),
                EventField("min_occurrences", "int", True, "Minimum pattern occurrences (hardcoded 2)"),
            ],
        ),
        BusEventSchema(
            name="incidents_to_learner",
            source_subsystem="governance.mandatory_gate",
            target_subsystem="memory.evolution.incident_learner",
            payload_type="IncidentLearningTrigger",
            description=(
                "When governance gate denies an action, notify IncidentLearner. "
                "Monkey-patches gate.check (stacks on v0.2 gate patches)."
            ),
            mechanism="monkey_patch",
            version="v0.3",
            is_bidirectional=False,
            payload_fields=[
                EventField("agent_id", "str", True, "Agent whose action was denied"),
                EventField("action", "str", True, "The denied action"),
                EventField("allowed", "bool", True, "Always False when this fires"),
                EventField("risk_level", "str", True, "Risk level from gate result"),
            ],
        ),
        BusEventSchema(
            name="optimizer_to_scheduler",
            source_subsystem="runtime.task_graph_optimizer",
            target_subsystem="task_graph.scheduler",
            payload_type="OptimizationResult",
            description=(
                "After optimization analysis, make results available to scheduler "
                "(read-only). Subscribes to Scheduler.on_event for GRAPH_COMPLETED, "
                "stores result as scheduler._latest_optimization."
            ),
            mechanism="callback",
            version="v0.3",
            is_bidirectional=False,
            payload_fields=[
                EventField("graph_id", "str", False, "Graph ID from event data"),
                EventField("estimated_improvement", "float", True, "Estimated improvement ratio"),
                EventField("bottleneck_count", "int", True, "Number of bottlenecks identified"),
            ],
        ),
        BusEventSchema(
            name="context_costs",
            source_subsystem="context.injection_logger",
            target_subsystem="context.context_economy.cost_accountant",
            payload_type="InjectionCostRecord",
            description=(
                "When InjectionLogger logs an injection, also record in "
                "ContextCostAccountant. Subscribes to InjectionLogger.on_injection."
            ),
            mechanism="callback",
            version="v0.3",
            is_bidirectional=False,
            payload_fields=[
                EventField("agent_id", "str", True, "Agent receiving the injection"),
                EventField("task_id", "str", True, "Task ID (defaults to 'unknown')"),
                EventField("operation", "str", True, "CostOperation.INJECTION"),
                EventField("tokens", "int", True, "Tokens consumed"),
                EventField("source", "str", True, "Always 'context.injection_logger'"),
                EventField("utility_score", "float", True, "Top relevance score (defaults to 0.0)"),
            ],
        ),
        BusEventSchema(
            name="budget_to_economy",
            source_subsystem="context.budget_manager",
            target_subsystem="context.context_economy.token_economy",
            payload_type="BudgetAllocationTracking",
            description=(
                "Connect BudgetManager spend events to TokenEconomy tracking. "
                "Monkey-patches budget_manager.allocate."
            ),
            mechanism="monkey_patch",
            version="v0.3",
            is_bidirectional=False,
            payload_fields=[
                EventField("agent_id", "str", True, "Agent requesting allocation"),
                EventField("tokens", "int", True, "Number of tokens allocated"),
            ],
        ),
        BusEventSchema(
            name="attention_runtime",
            source_subsystem="somatic.bus",
            target_subsystem="somatic.attention_runtime",
            payload_type="SomaticSignalForward",
            description=(
                "Route SignalBus signals through SomaticAttentionRuntime.process_signal() "
                "pipeline. Subscribes via bus.on_signal or bus.subscribe."
            ),
            mechanism="callback",
            version="v0.3",
            is_bidirectional=False,
            payload_fields=[
                EventField("signal", "SomaticSignal", True, "Full somatic signal object forwarded to runtime"),
            ],
        ),
        BusEventSchema(
            name="throttle_to_scheduler",
            source_subsystem="somatic.attention_runtime.throttle",
            target_subsystem="task_graph.scheduler",
            payload_type="ThrottleSchedulerAdjustment",
            description=(
                "When throttle state changes, adjust scheduler max_concurrent. "
                "Monkey-patches throttle.update to recalculate based on "
                "parallelism_factor."
            ),
            mechanism="monkey_patch",
            version="v0.3",
            is_bidirectional=False,
            payload_fields=[
                EventField("parallelism_factor", "float", True, "Current throttle parallelism factor"),
                EventField("original_max_concurrent", "int", True, "Scheduler max_concurrent before throttle"),
                EventField("new_max_concurrent", "int", True, "Adjusted max_concurrent (min 1)"),
            ],
        ),
        BusEventSchema(
            name="cognition_tracing",
            source_subsystem="governance.mandatory_gate",
            target_subsystem="observability.cognition_tracer",
            payload_type="GovernanceCognitionTrace",
            description=(
                "When governance gate checks occur, trace them in CognitionTracer. "
                "Monkey-patches gate.check (stacks on existing gate patches). "
                "Records DecisionType.GOVERNANCE with timing."
            ),
            mechanism="monkey_patch",
            version="v0.3",
            is_bidirectional=False,
            payload_fields=[
                EventField("decision_type", "str", True, "Always DecisionType.GOVERNANCE"),
                EventField("action", "str", True, "Action checked (truncated to 200 chars)"),
                EventField("agent_id", "str", True, "Agent requesting the check"),
                EventField("allowed", "bool", True, "Whether the gate allowed the action"),
                EventField("risk_level", "str", True, "RiskLevel name from gate result"),
                EventField("reason", "str", True, "Gate decision reason (truncated to 200-300 chars)"),
                EventField("duration", "float", True, "Time spent in gate check (seconds)"),
            ],
        ),
        BusEventSchema(
            name="memory_flow",
            source_subsystem="memory.kernel",
            target_subsystem="observability.memory_flow_tracer",
            payload_type="MemoryFlowTrace",
            description=(
                "When MemoryKernel recall/store happens, trace in MemoryFlowTracer. "
                "Monkey-patches both memory.recall and memory.store (stacks on "
                "v0.2 memory_metrics patch for recall)."
            ),
            mechanism="monkey_patch",
            version="v0.3",
            is_bidirectional=False,
            payload_fields=[
                EventField("operation", "str", True, "'recall' or 'store'"),
                EventField("query", "str", False, "Recall query (truncated to 200 chars, recall only)"),
                EventField("layer", "str", True, "Memory layer ('all' for recall, specific for store)"),
                EventField("results_count", "int", False, "Number of records returned (recall only)"),
                EventField("duration", "float", False, "Time spent in operation (recall only)"),
                EventField("hit_rate", "float", False, "Recall hit rate estimate (recall only)"),
                EventField("record_id", "str", False, "Stored record ID (store only)"),
                EventField("tags", "list[str]", False, "Tags attached to stored record (store only)"),
                EventField("size", "int", False, "Size of stored record (store only)"),
            ],
        ),
        BusEventSchema(
            name="evolution_audit",
            source_subsystem="memory.evolution",
            target_subsystem="governance.audit_log",
            payload_type="EvolutionAuditRecord",
            description=(
                "All evolution engine actions get logged to the governance audit log. "
                "Monkey-patches both reporter.generate_report and "
                "proposer.propose_from_patterns."
            ),
            mechanism="monkey_patch",
            version="v0.3",
            is_bidirectional=False,
            payload_fields=[
                EventField("action_type", "str", True, "'efficiency_report' or 'optimization_proposals'"),
                EventField("patterns_found", "int", False, "Pattern count (report only)"),
                EventField("proposals_generated", "int", False, "Proposal count (report only)"),
                EventField("risk_score", "float", False, "Report risk score (report only)"),
                EventField("proposals_count", "int", False, "Number of proposals (propose only)"),
                EventField("agent_id", "str", True, "Always 'evolution_engine'"),
            ],
        ),
        BusEventSchema(
            name="evolution_to_governance",
            source_subsystem="memory.evolution.proposer",
            target_subsystem="governance",
            payload_type="HighImpactProposalReview",
            description=(
                "Evolution proposals emit a REVIEW_REQUIRED governance event. "
                "Monkey-patches proposer.propose_from_patterns (stacks on "
                "evolution_audit patch). Only fires for high-impact proposals."
            ),
            mechanism="monkey_patch",
            version="v0.3",
            is_bidirectional=False,
            payload_fields=[
                EventField("high_impact_count", "int", True, "Number of high-impact proposals"),
                EventField("risk", "str", True, "Always 'REVIEW_REQUIRED'"),
                EventField("agent_id", "str", True, "Always 'evolution_engine'"),
                EventField("matched_policies", "list[str]", True, "Always ['evolution_governance']"),
            ],
        ),
    ]


class EventSchemaRegistry:
    """Registry of typed event schemas for all IntegrationBus connections."""

    def __init__(self, registry_guard: Any | None = None) -> None:
        self._schemas: dict[str, BusEventSchema] = {}
        self._registry_guard = registry_guard
        if self._registry_guard is None:
            try:
                from kernel.isolation.registry_guard import RegistryGuard
                from kernel.isolation.write_target import WriteTarget

                guard = RegistryGuard()
                guard.bind(
                    "event_schema_registry",
                    write_target=WriteTarget.INTEGRATION_BUS,
                    owner="architecture",
                )
                self._registry_guard = guard
            except ImportError:
                self._registry_guard = None
        for schema in _build_v02_schemas():
            self._schemas[schema.name] = schema
        for schema in _build_v03_schemas():
            self._schemas[schema.name] = schema
        logger.debug("EventSchemaRegistry initialized with %d schemas", len(self._schemas))

    def register_schema(
        self,
        schema: BusEventSchema,
        execution_context: Any | None = None,
    ) -> None:
        """Register or replace a schema (governed when execution_context provided)."""
        def _register() -> None:
            self._schemas[schema.name] = schema

        if execution_context is not None and self._registry_guard is not None:
            self._registry_guard.mutate(
                "event_schema_registry",
                _register,
                context=execution_context,
                operation="register_schema",
            )
            return
        _register()

    def get_schema(self, connection_name: str) -> BusEventSchema | None:
        return self._schemas.get(connection_name)

    def get_all_schemas(self) -> list[BusEventSchema]:
        return list(self._schemas.values())

    def get_by_subsystem(self, subsystem: str) -> list[BusEventSchema]:
        return [
            s for s in self._schemas.values()
            if subsystem in s.source_subsystem or subsystem in s.target_subsystem
        ]

    def get_by_mechanism(self, mechanism: str) -> list[BusEventSchema]:
        return [s for s in self._schemas.values() if s.mechanism == mechanism]

    def get_by_version(self, version: str) -> list[BusEventSchema]:
        return [s for s in self._schemas.values() if s.version == version]

    def validate_event(self, connection_name: str, payload: dict) -> EventValidationResult:
        schema = self._schemas.get(connection_name)
        if schema is None:
            return EventValidationResult(
                valid=False,
                connection_name=connection_name,
                errors=[f"Unknown connection: {connection_name}"],
            )

        errors: list[str] = []
        for f in schema.payload_fields:
            if f.required and f.name not in payload:
                errors.append(f"Missing required field: {f.name}")

        for key in payload:
            known = {f.name for f in schema.payload_fields}
            if key not in known:
                errors.append(f"Unexpected field: {key}")

        return EventValidationResult(
            valid=len(errors) == 0,
            connection_name=connection_name,
            errors=errors,
        )
