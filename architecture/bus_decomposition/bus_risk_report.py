"""Risk analysis generator for the IntegrationBus.

Produces a comprehensive BusRiskReport covering monkey-patch stacking,
callback lifecycle gaps, coupling depth, event propagation hazards,
and consistency issues like double-auditing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from architecture.bus_decomposition.connection_registry import ConnectionRegistry
from architecture.bus_decomposition.event_schema import EventSchemaRegistry

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RiskFinding:
    category: str
    severity: str
    title: str
    description: str
    affected_connections: list[str]
    recommendation: str


@dataclass
class BusRiskReport:
    findings: list[RiskFinding] = field(default_factory=list)
    risk_score: float = 0.0
    risk_level: str = "unknown"
    total_connections: int = 0
    monkey_patch_count: int = 0
    callback_count: int = 0
    max_stack_depth: int = 0
    generated_at: str = ""


class BusRiskReportGenerator:
    """Generates a risk analysis of the current IntegrationBus architecture."""

    def __init__(
        self,
        root_dir: Path,
        schema_registry: EventSchemaRegistry,
        connection_registry: ConnectionRegistry,
    ) -> None:
        self._root_dir = root_dir
        self._schemas = schema_registry
        self._connections = connection_registry

    def generate(self) -> BusRiskReport:
        findings: list[RiskFinding] = []
        findings.extend(self._analyze_monkey_patch_risks())
        findings.extend(self._analyze_callback_risks())
        findings.extend(self._analyze_coupling_risks())
        findings.extend(self._analyze_propagation_risks())
        findings.extend(self._analyze_consistency_risks())

        patches = self._connections.get_monkey_patches()
        callbacks = self._connections.get_callbacks()
        max_depth = max((c.stack_depth for c in patches), default=0)

        score = self._compute_overall_risk_score(findings)
        if score >= 0.8:
            level = "critical"
        elif score >= 0.6:
            level = "high"
        elif score >= 0.4:
            level = "medium"
        else:
            level = "low"

        return BusRiskReport(
            findings=findings,
            risk_score=score,
            risk_level=level,
            total_connections=len(self._schemas.get_all_schemas()),
            monkey_patch_count=len(patches),
            callback_count=len(callbacks),
            max_stack_depth=max_depth,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _analyze_monkey_patch_risks(self) -> list[RiskFinding]:
        findings: list[RiskFinding] = []

        findings.append(RiskFinding(
            category="monkey_patch",
            severity="critical",
            title="gate.check 4-deep monkey-patch stacking",
            description=(
                "MandatoryGate.check() is patched 4 layers deep: "
                "mandatory_gate_audit → tool_permission_somatic → "
                "incidents_to_learner → cognition_tracing. "
                "Each layer wraps the previous, creating a fragile call chain. "
                "If any middle layer throws an unhandled exception, all outer "
                "layers are bypassed and the original check result may be lost."
            ),
            affected_connections=[
                "mandatory_gate_audit",
                "tool_permission_somatic",
                "incidents_to_learner",
                "cognition_tracing",
            ],
            recommendation=(
                "Replace the monkey-patch chain with a pre/post hook mechanism "
                "or event-based pub/sub on gate.check. Each observer should "
                "subscribe independently rather than wrapping the method."
            ),
        ))

        findings.append(RiskFinding(
            category="monkey_patch",
            severity="high",
            title="memory.recall 2-deep monkey-patch stacking",
            description=(
                "memory.recall is patched by v0.2 memory_metrics and then "
                "by v0.3 memory_flow. The v0.3 layer wraps whatever "
                "memory.recall points to at wire_v03() time, which is the "
                "already-patched v0.2 version. Unwiring v0.3 restores the "
                "v0.2 patch, not the original."
            ),
            affected_connections=["memory_metrics", "memory_flow"],
            recommendation=(
                "Use a pre/post hook list on memory.recall so both observers "
                "can subscribe independently. This eliminates ordering dependency."
            ),
        ))

        findings.append(RiskFinding(
            category="monkey_patch",
            severity="high",
            title="proposer.propose_from_patterns 2-deep stacking",
            description=(
                "propose_from_patterns is patched by evolution_audit and then "
                "by evolution_to_governance. The governance layer stacks on "
                "the audit layer, so unwiring one breaks the other."
            ),
            affected_connections=["evolution_audit", "evolution_to_governance"],
            recommendation=(
                "Refactor to a hook-based pattern where both audit and "
                "governance subscribe to a post-propose event independently."
            ),
        ))

        findings.append(RiskFinding(
            category="monkey_patch",
            severity="high",
            title="Partial unwire coverage — only scheduler config restored",
            description=(
                "unwire() only restores scheduler max_concurrent. The 6 "
                "monkey-patched methods (validator.validate, memory.recall, "
                "gate.check, kernel.health, telemetry.complete_task, and later "
                "v0.3 patches) are NOT restored. unwire_v03() restores some "
                "but skips validator.validate and analytics patches entirely."
            ),
            affected_connections=[
                "governance_to_audit",
                "memory_metrics",
                "mandatory_gate_audit",
                "tool_permission_somatic",
                "analytics_to_health",
                "agent_decision_log",
            ],
            recommendation=(
                "Store all original method references at wire time and "
                "restore them in unwire(). Use a registry to track "
                "which methods are patched and their original values."
            ),
        ))

        findings.append(RiskFinding(
            category="monkey_patch",
            severity="medium",
            title="Exception bypass in patch chains",
            description=(
                "Most monkey-patch wrappers call the original method first, "
                "then perform side-effects. If the side-effect throws, the "
                "original result is still returned (good). But some wrappers "
                "like incidents_to_learner call the stacked gate.check — if "
                "any layer in the stack throws, the gate check fails silently."
            ),
            affected_connections=[
                "incidents_to_learner",
                "cognition_tracing",
                "tool_permission_somatic",
            ],
            recommendation=(
                "Wrap each side-effect in try/except individually to ensure "
                "the primary method result is always returned regardless of "
                "observer failures."
            ),
        ))

        return findings

    def _analyze_callback_risks(self) -> list[RiskFinding]:
        findings: list[RiskFinding] = []

        findings.append(RiskFinding(
            category="callback",
            severity="high",
            title="No callback unsubscription mechanism",
            description=(
                "AttentionManager.on_change(), Scheduler.on_event(), "
                "InjectionLogger.on_injection(), and SignalCorrelator.on_correlation() "
                "accept callback registrations but provide no way to unsubscribe. "
                "This means unwire()/unwire_v03() cannot remove callback-based "
                "connections, leading to listener leaks."
            ),
            affected_connections=[
                "somatic_to_scheduler",
                "somatic_to_context",
                "attention_to_governance",
                "attention_to_agents",
                "tasks_to_tracer",
                "failure_propagation",
                "checkpoint_cleanup",
                "injection_to_tracer",
                "signal_correlator",
                "execution_to_patterns",
                "optimizer_to_scheduler",
                "context_costs",
                "attention_runtime",
            ],
            recommendation=(
                "Add return-unsubscribe pattern to all on_event/on_change/on_signal "
                "APIs: `unsub = scheduler.on_event(cb)` returns a callable that "
                "removes the callback. Store unsubscribe handles in IntegrationBus."
            ),
        ))

        findings.append(RiskFinding(
            category="callback",
            severity="medium",
            title="AttentionManager.on_change has 4 subscribers without ordering guarantees",
            description=(
                "Four separate callbacks are registered on AttentionManager.on_change: "
                "somatic_to_scheduler, somatic_to_context, attention_to_governance, "
                "and attention_to_agents. Execution order depends on registration order, "
                "which is not documented or contractual."
            ),
            affected_connections=[
                "somatic_to_scheduler",
                "somatic_to_context",
                "attention_to_governance",
                "attention_to_agents",
            ],
            recommendation=(
                "Define explicit priority levels for callbacks or document "
                "that order is non-deterministic. Consider making scheduler "
                "adjustment highest priority."
            ),
        ))

        findings.append(RiskFinding(
            category="callback",
            severity="medium",
            title="Scheduler.on_event has 5+ subscribers with overlapping filters",
            description=(
                "Scheduler.on_event receives tasks_to_tracer (all events), "
                "failure_propagation (TASK_FAILED), checkpoint_cleanup "
                "(GRAPH_COMPLETED/FAILED), execution_to_patterns (GRAPH_COMPLETED), "
                "and optimizer_to_scheduler (GRAPH_COMPLETED). All fire for every "
                "event; filtering happens inside each handler."
            ),
            affected_connections=[
                "tasks_to_tracer",
                "failure_propagation",
                "checkpoint_cleanup",
                "execution_to_patterns",
                "optimizer_to_scheduler",
            ],
            recommendation=(
                "Support event-type-specific subscriptions to avoid wasted "
                "dispatch: scheduler.on_event(GRAPH_COMPLETED, handler) instead "
                "of filtering inside each handler."
            ),
        ))

        return findings

    def _analyze_coupling_risks(self) -> list[RiskFinding]:
        findings: list[RiskFinding] = []

        findings.append(RiskFinding(
            category="coupling",
            severity="medium",
            title="IntegrationBus holds entire AmbientKernel reference",
            description=(
                "IntegrationBus.__init__ takes the full AmbientKernel instance "
                "and accesses kernel.somatic.attention, kernel.task_graph.scheduler, "
                "kernel.governance.validator, kernel.memory, kernel.context, "
                "kernel.observability, kernel.agents, and more. This makes "
                "IntegrationBus tightly coupled to the kernel's internal structure."
            ),
            affected_connections=[],
            recommendation=(
                "Pass only the specific subsystem references needed, or define "
                "a narrow BusContext interface that exposes only the APIs the bus "
                "uses. This allows testing and decoupled evolution."
            ),
        ))

        findings.append(RiskFinding(
            category="coupling",
            severity="medium",
            title="Bus accesses private attributes on kernel internals",
            description=(
                "Several connections access private attributes: "
                "executor._current_graph, bm._original_total_budget, "
                "scheduler._latest_optimization. This creates fragile coupling "
                "to implementation details that may change without notice."
            ),
            affected_connections=[
                "failure_propagation",
                "somatic_to_context",
                "optimizer_to_scheduler",
            ],
            recommendation=(
                "Expose public APIs for the data the bus needs: "
                "executor.current_graph property, budget_manager.original_budget "
                "property, scheduler.latest_optimization property."
            ),
        ))

        findings.append(RiskFinding(
            category="coupling",
            severity="low",
            title="Circular subsystem dependencies via bus wiring",
            description=(
                "The bus creates implicit bidirectional coupling: "
                "somatic → scheduler and scheduler → somatic (via callbacks), "
                "governance → audit and audit → governance (via evolution). "
                "While the bus is unidirectional per connection, the overall "
                "topology creates cycles that make reasoning about data flow harder."
            ),
            affected_connections=[
                "somatic_to_scheduler",
                "throttle_to_scheduler",
                "evolution_audit",
                "evolution_to_governance",
            ],
            recommendation=(
                "Map and document all cycles. Ensure no synchronous cycle exists "
                "where A calls B which calls A in the same call stack."
            ),
        ))

        return findings

    def _analyze_propagation_risks(self) -> list[RiskFinding]:
        findings: list[RiskFinding] = []

        findings.append(RiskFinding(
            category="propagation",
            severity="medium",
            title="Synchronous dispatch — slow handler blocks all subsequent handlers",
            description=(
                "All bus connections dispatch synchronously. A slow handler "
                "in one callback (e.g. pattern_miner.mine_success_patterns) "
                "blocks all subsequent handlers for the same event. There is "
                "no timeout or async dispatch mechanism."
            ),
            affected_connections=[
                "execution_to_patterns",
                "optimizer_to_scheduler",
                "incidents_to_learner",
            ],
            recommendation=(
                "Add an optional async dispatch mode to the bus that runs "
                "handlers in separate tasks with configurable timeouts. "
                "Start with the most expensive handlers (pattern mining, "
                "optimization)."
            ),
        ))

        findings.append(RiskFinding(
            category="propagation",
            severity="medium",
            title="Uncontrolled event cascades from attention changes",
            description=(
                "A single AttentionState change fires 4 handlers simultaneously: "
                "scheduler adjustment, context budget scaling, governance sensitivity, "
                "and agent parallelism. Each handler may trigger further side-effects "
                "(e.g. scheduler change triggers on_event callbacks). No circuit "
                "breaker limits cascade depth."
            ),
            affected_connections=[
                "somatic_to_scheduler",
                "somatic_to_context",
                "attention_to_governance",
                "attention_to_agents",
            ],
            recommendation=(
                "Implement cascade depth tracking and a circuit breaker. "
                "Log a warning if cascade depth exceeds a configurable threshold."
            ),
        ))

        findings.append(RiskFinding(
            category="propagation",
            severity="low",
            title="drift_to_somatic → attention → scheduler cascade potential",
            description=(
                "DriftDetector.detect can emit a pressure signal to SomaticSignalBus, "
                "which routes through attention_runtime (process_signal), which may "
                "change AttentionState, which then triggers 4 more handlers. This "
                "multi-hop cascade is not bounded."
            ),
            affected_connections=[
                "drift_to_somatic",
                "attention_runtime",
                "somatic_to_scheduler",
            ],
            recommendation=(
                "Document the cascade path. Add a max-depth guard to prevent "
                "recursive cascades through the somatic → attention → scheduler path."
            ),
        ))

        return findings

    def _analyze_consistency_risks(self) -> list[RiskFinding]:
        findings: list[RiskFinding] = []

        findings.append(RiskFinding(
            category="consistency",
            severity="medium",
            title="Double-auditing: MandatoryGate + IntegrationBus governance→audit wiring",
            description=(
                "MandatoryGate already performs its own audit logging internally. "
                "The governance_to_audit bus connection adds a second audit record "
                "for every validation decision. This means each validation produces "
                "duplicate audit entries from two different paths."
            ),
            affected_connections=[
                "governance_to_audit",
                "mandatory_gate_audit",
            ],
            recommendation=(
                "Audit at one point only. Either let MandatoryGate own its "
                "audit logging or let the bus own it, but not both. "
                "Introduce a shared audit interface to prevent duplication."
            ),
        ))

        findings.append(RiskFinding(
            category="consistency",
            severity="medium",
            title="Race condition: concurrent scheduler config modifications",
            description=(
                "Both somatic_to_scheduler (v0.2) and throttle_to_scheduler (v0.3) "
                "modify scheduler.config.max_concurrent. If an attention change and "
                "a throttle update happen concurrently, the last write wins without "
                "coordination."
            ),
            affected_connections=[
                "somatic_to_scheduler",
                "throttle_to_scheduler",
            ],
            recommendation=(
                "Introduce a single concurrency policy resolver that takes "
                "both attention state and throttle state as inputs and produces "
                "a single max_concurrent value."
            ),
        ))

        findings.append(RiskFinding(
            category="consistency",
            severity="low",
            title="Event log capped at 500 with silent discard",
            description=(
                "IntegrationBus.event_log is capped at _max_log=500 entries. "
                "When the cap is reached, oldest events are silently discarded. "
                "No metric tracks how many events have been lost."
            ),
            affected_connections=[],
            recommendation=(
                "Add a dropped_events counter and emit a warning when the log "
                "wraps. Consider writing older events to a persistent store "
                "before discarding."
            ),
        ))

        return findings

    def _compute_overall_risk_score(self, findings: list[RiskFinding]) -> float:
        if not findings:
            return 0.0

        weights = {"critical": 1.0, "high": 0.7, "medium": 0.4, "low": 0.15}
        total_weight = 0.0
        for f in findings:
            total_weight += weights.get(f.severity, 0.2)

        max_possible = len(findings) * 1.0
        raw = total_weight / max_possible if max_possible > 0 else 0.0
        return round(min(1.0, raw), 3)
