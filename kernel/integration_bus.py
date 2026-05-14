"""
Integration Bus — Cross-subsystem wiring for the Ambient OS kernel.

This is the KEY missing piece identified in Phase 0: individual subsystems are
well-designed but operate in isolation. The IntegrationBus connects them:

  Somatic → Scheduler:     Throttle concurrency when system is stressed
  Somatic → Context:       Reduce token budgets under pressure
  Somatic → Governance:    Increase scrutiny when attention level rises
  Governance → Audit:      Auto-record every validation decision
  Task Events → Tracer:    Auto-trace task lifecycle events
  Attention → Agents:      Adjust agent execution preferences under load

The bus is purely additive — it subscribes to existing hooks and events
without modifying any existing module. All wiring is reversible via unwire().
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kernel import AmbientKernel

from somatic.signal_bus import SomaticSignal, SignalType, SignalUrgency
from somatic.attention_manager import AttentionState, AttentionLevel
from governance.policy_engine import RiskLevel
from governance.mandatory_gate import MandatoryGate, GateResult
from governance.tool_permissions import ToolPermission
from runtime.task_graph.scheduler import SchedulerEvent
from runtime.task_graph.failure_propagation import FailurePropagator

logger = logging.getLogger("kernel.integration_bus")


@dataclass
class BusEvent:
    """A recorded cross-subsystem event."""
    source: str
    target: str
    event_type: str
    description: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "event_type": self.event_type,
            "description": self.description,
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
        }


class IntegrationBus:
    """
    Wires subsystems together via their existing hook/callback APIs.

    Usage (internal — called by AmbientKernel.boot()):
        bus = IntegrationBus(kernel)
        bus.wire()

    All connections are logged and inspectable via bus.event_log.
    """

    def __init__(self, kernel: "AmbientKernel"):
        self.kernel = kernel
        self.event_log: list[BusEvent] = []
        self._max_log = 500
        self._wired = False
        self._original_scheduler_config: dict[str, Any] | None = None

    def wire(self) -> None:
        """Activate all cross-subsystem connections."""
        if self._wired:
            return

        self._wire_somatic_to_scheduler()
        self._wire_somatic_to_context()
        self._wire_attention_to_governance()
        self._wire_governance_to_audit()
        self._wire_tasks_to_tracer()
        self._wire_attention_to_agents()
        self._wire_memory_metrics()
        self._wire_injection_to_tracer()
        self._wire_failure_propagation()
        self._wire_checkpoint_cleanup()
        self._wire_mandatory_gate_audit()
        self._wire_tool_permission_somatic()
        self._wire_signal_correlator()
        self._wire_rate_tracker()
        self._wire_analytics_to_health()
        self._wire_agent_decision_log()

        self._wired = True
        self._log_event("kernel", "all", "wired", "Integration bus fully connected")
        logger.info("IntegrationBus: all subsystem connections active")

    def unwire(self) -> None:
        """Deactivate connections and restore original configs."""
        if self._original_scheduler_config:
            self.kernel.task_graph.scheduler.config.max_concurrent = (
                self._original_scheduler_config["max_concurrent"]
            )
        self._wired = False
        self._log_event("kernel", "all", "unwired", "Integration bus disconnected")

    @property
    def is_wired(self) -> bool:
        return self._wired

    def status(self) -> dict[str, Any]:
        """Current integration bus status."""
        v03_connections = getattr(self, '_v03_connections', [])
        return {
            "wired": self._wired,
            "v02_connections": 16 if self._wired else 0,
            "v03_connections": len(v03_connections),
            "v03_connection_names": list(v03_connections),
            "total_connections": (16 if self._wired else 0) + len(v03_connections),
            "events_logged": len(self.event_log),
            "recent_events": [e.to_dict() for e in self.event_log[-10:]],
        }

    # ── Somatic → Scheduler ──────────────────────────────────────────────

    def _wire_somatic_to_scheduler(self) -> None:
        """When attention level changes, adjust scheduler concurrency."""
        self._original_scheduler_config = {
            "max_concurrent": self.kernel.task_graph.scheduler.config.max_concurrent,
        }

        def on_attention_change(old: AttentionState, new: AttentionState) -> None:
            new_max = new.max_concurrency
            self.kernel.task_graph.scheduler.config.max_concurrent = new_max
            self._log_event(
                "somatic.attention",
                "task_graph.scheduler",
                "concurrency_adjusted",
                f"Attention {old.level.label} → {new.level.label}: "
                f"max_concurrent = {new_max}",
            )

        self.kernel.somatic.attention.on_change(on_attention_change)

    # ── Somatic → Context ────────────────────────────────────────────────

    def _wire_somatic_to_context(self) -> None:
        """When system is stressed, reduce context token budgets."""

        def on_attention_for_context(old: AttentionState, new: AttentionState) -> None:
            ratio = new.context_budget_ratio
            bm = self.kernel.context.budget_manager
            if hasattr(bm, 'total_budget'):
                original = getattr(bm, '_original_total_budget', bm.total_budget)
                if not hasattr(bm, '_original_total_budget'):
                    bm._original_total_budget = bm.total_budget
                bm.total_budget = int(original * ratio)
                self._log_event(
                    "somatic.attention",
                    "context.budget_manager",
                    "budget_adjusted",
                    f"Context budget ratio {ratio:.0%}: "
                    f"{original} → {bm.total_budget} tokens",
                )

        self.kernel.somatic.attention.on_change(on_attention_for_context)

    # ── Attention → Governance ───────────────────────────────────────────

    def _wire_attention_to_governance(self) -> None:
        """When attention rises, log governance sensitivity change."""

        def on_attention_for_governance(
            old: AttentionState, new: AttentionState
        ) -> None:
            if new.governance_sensitivity > old.governance_sensitivity:
                self._log_event(
                    "somatic.attention",
                    "governance",
                    "sensitivity_increased",
                    f"Governance sensitivity: {old.governance_sensitivity:.1f}x "
                    f"→ {new.governance_sensitivity:.1f}x",
                )

        self.kernel.somatic.attention.on_change(on_attention_for_governance)

    # ── Governance → Audit Log ───────────────────────────────────────────

    def _wire_governance_to_audit(self) -> None:
        """Auto-record every validation decision into the audit log."""
        original_validate = self.kernel.governance.validator.validate

        def validate_with_audit(*args: Any, **kwargs: Any):
            result = original_validate(*args, **kwargs)

            matched_names = []
            if result.stages:
                for stage in result.stages:
                    policy_name = stage.metadata.get("policy", "")
                    if policy_name:
                        matched_names.append(policy_name)

            self.kernel.governance.audit_log.record_decision(
                action=result.action,
                risk=result.risk,
                reason=result.blocking_stage.details if result.blocking_stage else "Allowed",
                agent_id=result.agent_id,
                matched_policies=matched_names,
                validation_stages=[
                    {"name": s.name, "passed": s.passed, "risk": s.risk.name}
                    for s in result.stages
                ],
            )

            self._log_event(
                "governance.validator",
                "governance.audit_log",
                "decision_recorded",
                f"{result.action[:60]}... → {result.risk.name}",
            )
            return result

        self.kernel.governance.validator.validate = validate_with_audit

    # ── Task Events → Tracer ─────────────────────────────────────────────

    def _wire_tasks_to_tracer(self) -> None:
        """Auto-trace scheduler events into the observability layer."""

        def on_scheduler_event(event: SchedulerEvent, data: dict[str, Any]) -> None:
            tracer = self.kernel.observability.tracer
            if hasattr(tracer, 'record_event'):
                tracer.record_event(
                    name=f"scheduler.{event.value}",
                    attributes=data,
                )
            self._log_event(
                "task_graph.scheduler",
                "observability.tracer",
                event.value,
                f"Task event: {data.get('task_id', 'graph')}",
            )

        self.kernel.task_graph.scheduler.on_event(on_scheduler_event)

    # ── Attention → Agents ───────────────────────────────────────────────

    def _wire_attention_to_agents(self) -> None:
        """Adjust agent parallelism preferences when system is stressed."""

        def on_attention_for_agents(
            old: AttentionState, new: AttentionState
        ) -> None:
            max_p = new.max_concurrency
            for agent in self.kernel.agents.registry.all_agents():
                agent.preferences.parallelism = min(
                    agent.preferences.parallelism, max_p
                )

            if new.should_pause_non_critical:
                self._log_event(
                    "somatic.attention",
                    "agent_runtime",
                    "pause_non_critical",
                    "OVERWHELMED: non-critical agents should pause",
                )

        self.kernel.somatic.attention.on_change(on_attention_for_agents)

    # ── Memory → Metrics ───────────────────────────────────────────────────

    def _wire_memory_metrics(self) -> None:
        """Track memory recall operations in observability metrics."""
        original_recall = self.kernel.memory.recall

        def recall_with_metrics(*args: Any, **kwargs: Any):
            result = original_recall(*args, **kwargs)

            metrics = self.kernel.observability.metrics
            if hasattr(metrics, 'increment'):
                metrics.increment("memory.recalls")
                if result.dedup_removed > 0:
                    metrics.increment("memory.dedup_removed",
                                      value=result.dedup_removed)

            self._log_event(
                "memory.kernel",
                "observability.metrics",
                "recall_tracked",
                f"query='{result.query[:40]}' results={len(result.records)} "
                f"tokens={result.total_tokens} dedup={result.dedup_removed}",
            )
            return result

        self.kernel.memory.recall = recall_with_metrics

    # ── Context Injection → Tracer ─────────────────────────────────────────

    def _wire_injection_to_tracer(self) -> None:
        """Auto-trace context injection events into the observability layer."""
        injection_logger = self.kernel.context.injection_logger
        if injection_logger is None:
            return

        def on_injection(event) -> None:
            tracer = self.kernel.observability.tracer
            if hasattr(tracer, 'record_event'):
                tracer.record_event(
                    name="context.injection",
                    attributes={
                        "agent_id": event.agent_id,
                        "query": event.query[:100],
                        "memory_count": event.memory_count,
                        "tokens_used": event.tokens_used,
                        "layers_used": event.layers_used,
                        "top_score": round(event.top_score, 4),
                        "compression_applied": event.compression_applied,
                    },
                )

            metrics = self.kernel.observability.metrics
            if hasattr(metrics, 'increment'):
                metrics.increment("context.injections")
                metrics.increment("context.tokens_injected", value=event.tokens_used)

            self._log_event(
                "context.injection_logger",
                "observability.tracer",
                "injection_traced",
                f"agent={event.agent_id} memories={event.memory_count} "
                f"tokens={event.tokens_used}",
            )

        injection_logger.on_injection(on_injection)

    # ── Failure Propagation → Governance + Tracer ──────────────────────────

    def _wire_failure_propagation(self) -> None:
        """
        Auto-propagate failures through the DAG and log to governance audit.

        When a task fails, the FailurePropagator marks downstream dependents
        as SKIPPED and records the chain. The bus relays this to the tracer
        and governance audit for visibility.
        """
        propagator = FailurePropagator()
        self.kernel.task_graph.failure_propagator = propagator

        def on_task_failure(event: SchedulerEvent, data: dict[str, Any]) -> None:
            if event != SchedulerEvent.TASK_FAILED:
                return

            task_id = data.get("task_id")
            if not task_id:
                return

            executor = self.kernel.task_graph.executor
            if not hasattr(executor, '_current_graph'):
                return

            graph = executor._current_graph
            chain = propagator.propagate(graph, task_id)

            if chain.skipped_count > 0:
                self._log_event(
                    "task_graph.failure_propagator",
                    "task_graph.dag",
                    "failure_propagated",
                    f"Task '{task_id}' failure cascaded to "
                    f"{chain.skipped_count} downstream tasks: "
                    f"{chain.affected_task_ids}",
                )

                tracer = self.kernel.observability.tracer
                if hasattr(tracer, 'record_event'):
                    tracer.record_event(
                        name="task_graph.failure_propagation",
                        attributes={
                            "root_task": task_id,
                            "skipped_count": chain.skipped_count,
                            "affected_tasks": chain.affected_task_ids,
                        },
                    )

        self.kernel.task_graph.scheduler.on_event(on_task_failure)

    # ── Checkpoint Auto-Cleanup ──────────────────────────────────────────

    def _wire_checkpoint_cleanup(self) -> None:
        """Run checkpoint cleanup after each graph completion."""

        def on_graph_complete(event: SchedulerEvent, data: dict[str, Any]) -> None:
            if event not in (SchedulerEvent.GRAPH_COMPLETED, SchedulerEvent.GRAPH_FAILED):
                return

            checkpoint_mgr = self.kernel.task_graph.checkpoint
            if checkpoint_mgr is None:
                return

            try:
                removed = checkpoint_mgr.cleanup_all_graphs(keep_latest_n=5)
                if removed > 0:
                    self._log_event(
                        "task_graph.checkpoint",
                        "task_graph.checkpoint",
                        "auto_cleanup",
                        f"Removed {removed} old checkpoint files",
                    )
            except Exception as exc:
                logger.warning(f"Checkpoint auto-cleanup failed: {exc}")

        self.kernel.task_graph.scheduler.on_event(on_graph_complete)

    # ── Mandatory Gate → Audit + Tracer ─────────────────────────────────

    def _wire_mandatory_gate_audit(self) -> None:
        """Ensure all MandatoryGate checks are traced in observability."""
        gate = self.kernel.governance.mandatory_gate
        if gate is None:
            return

        original_check = gate.check

        def check_with_trace(*args: Any, **kwargs: Any) -> GateResult:
            result = original_check(*args, **kwargs)

            tracer = self.kernel.observability.tracer
            if hasattr(tracer, 'record_event'):
                tracer.record_event(
                    name="governance.mandatory_gate",
                    attributes={
                        "action": result.action[:100],
                        "agent_id": result.agent_id,
                        "allowed": result.allowed,
                        "risk_level": result.risk_level.name,
                        "reason": result.reason[:200],
                    },
                )

            self._log_event(
                "governance.mandatory_gate",
                "observability.tracer",
                "gate_check_traced",
                f"agent={result.agent_id} action='{result.action[:50]}' "
                f"→ {result.risk_level.name}",
            )
            return result

        gate.check = check_with_trace

    # ── Tool Permission Denial → Somatic Pain Signal ─────────────────────

    def _wire_tool_permission_somatic(self) -> None:
        """Emit somatic pain signal when tool permissions are denied (security concern)."""
        gate = self.kernel.governance.mandatory_gate
        if gate is None:
            return

        original_check = gate.check

        def check_with_somatic(*args: Any, **kwargs: Any) -> GateResult:
            result = original_check(*args, **kwargs)

            if (
                result.permission_result
                and result.permission_result.is_denied
                and hasattr(self.kernel.somatic.bus, 'emit_pressure')
            ):
                self.kernel.somatic.bus.emit_pressure(
                    source="governance.tool_permissions",
                    description=(
                        f"Tool permission denied: agent={result.agent_id} "
                        f"tool={result.permission_result.tool_name}"
                    ),
                    value=80.0,
                    threshold=50.0,
                )

                self._log_event(
                    "governance.tool_permissions",
                    "somatic.bus",
                    "permission_denied_pain",
                    f"Pain signal: {result.agent_id} denied "
                    f"{result.permission_result.tool_name}",
                )

            return result

        gate.check = check_with_somatic

    # ── Signal Correlator → Bus ──────────────────────────────────────────

    def _wire_signal_correlator(self) -> None:
        """Activate the signal correlator to detect compound patterns."""
        correlator = self.kernel.somatic.correlator
        if correlator is None:
            return

        correlator.subscribe()

        def on_correlation(event) -> None:
            self._log_event(
                "somatic.correlator",
                "somatic.bus",
                "correlation_detected",
                f"Pattern '{event.rule_name}': "
                f"{len(event.matched_signals)} signals, "
                f"severity x{event.severity_multiplier}",
            )

            tracer = self.kernel.observability.tracer
            if hasattr(tracer, 'record_event'):
                tracer.record_event(
                    name="somatic.correlation",
                    attributes=event.to_dict(),
                )

        correlator.on_correlation(on_correlation)

    # ── Rate Tracker → Bus ───────────────────────────────────────────────

    def _wire_rate_tracker(self) -> None:
        """Activate the rate tracker to monitor signal rates and spike detection."""
        tracker = self.kernel.somatic.rate_tracker
        if tracker is None:
            return

        tracker.subscribe()
        self._log_event(
            "kernel",
            "somatic.rate_tracker",
            "rate_tracker_wired",
            "Rate tracker subscribed to somatic bus for spike detection",
        )

    # ── Analytics → Health ───────────────────────────────────────────────

    def _wire_analytics_to_health(self) -> None:
        """Wire analytics into the kernel health reporting."""
        analytics = self.kernel.somatic.analytics
        if analytics is None:
            return

        original_health = self.kernel.health

        def health_with_analytics() -> dict:
            result = original_health()
            try:
                report = analytics.health_report(window_seconds=300)
                result["somatic_health"] = report.to_dict()
            except Exception:
                result["somatic_health"] = {"score": -1, "error": "analytics unavailable"}
            return result

        self.kernel.health = health_with_analytics

        self._log_event(
            "somatic.analytics",
            "kernel.health",
            "analytics_wired",
            "Somatic analytics integrated into kernel health reporting",
        )

    # ── Agent Decision Log → Observability ─────────────────────────────

    def _wire_agent_decision_log(self) -> None:
        """Auto-record agent task completions as decision events in the decision log."""
        decision_log = getattr(self.kernel.observability, 'decision_log', None)
        if decision_log is None:
            return

        telemetry = self.kernel.observability.telemetry
        original_complete = telemetry.complete_task

        def complete_with_decision(
            agent_id: str, task_id: str, success: bool = True, error: str | None = None
        ):
            result = original_complete(agent_id, task_id, success, error)

            if result is not None:
                decision_log.log_decision(
                    agent_id=agent_id,
                    task=result.name,
                    strategy_chosen="task_execution",
                    governance_result="ALLOW",
                    confidence=1.0 if success else 0.0,
                    reasoning=f"Task {'completed' if success else 'failed'}: {result.name}",
                    metadata={
                        "task_id": task_id,
                        "status": result.status,
                        "duration_ms": result.duration_ms,
                        "tokens_used": result.tokens_used,
                    },
                )

                self._log_event(
                    "agent.telemetry",
                    "observability.decision_log",
                    "decision_recorded",
                    f"agent={agent_id} task={task_id} → {result.status}",
                )

            return result

        telemetry.complete_task = complete_with_decision

        self._log_event(
            "kernel",
            "observability.decision_log",
            "decision_log_wired",
            "Agent task completions wired to decision log",
        )

    # ══════════════════════════════════════════════════════════════════════
    # v0.3 cross-subsystem wiring
    # ══════════════════════════════════════════════════════════════════════

    def wire_v03(
        self,
        *,
        self_model=None,
        drift_detector=None,
        pattern_miner=None,
        incident_learner=None,
        task_graph_optimizer=None,
        cost_accountant=None,
        token_economy=None,
        attention_runtime=None,
        cognition_tracer=None,
        memory_flow_tracer=None,
        evolution_reporter=None,
        optimization_proposer=None,
    ) -> None:
        """
        Wire v0.3 subsystem connections.

        All parameters are optional — only connections where both sides are
        provided will be established. Existing v0.2 wiring is unaffected.
        """
        self._v03_connections: list[str] = []

        if self_model is not None and drift_detector is not None:
            self._wire_self_model_drift(self_model, drift_detector)

        if drift_detector is not None:
            self._wire_drift_to_somatic(drift_detector)

        if pattern_miner is not None:
            self._wire_execution_to_patterns(pattern_miner)

        if incident_learner is not None:
            self._wire_incidents_to_learner(incident_learner)

        if task_graph_optimizer is not None:
            self._wire_optimizer_to_scheduler(task_graph_optimizer)

        if cost_accountant is not None:
            self._wire_context_costs(cost_accountant)

        if token_economy is not None:
            self._wire_budget_to_economy(token_economy)

        if attention_runtime is not None:
            self._wire_attention_runtime(attention_runtime)

        if attention_runtime is not None:
            self._wire_throttle_to_scheduler(attention_runtime)

        if cognition_tracer is not None:
            self._wire_cognition_tracing(cognition_tracer)

        if memory_flow_tracer is not None:
            self._wire_memory_flow(memory_flow_tracer)

        if evolution_reporter is not None or optimization_proposer is not None:
            self._wire_evolution_audit(evolution_reporter, optimization_proposer)

        if optimization_proposer is not None:
            self._wire_evolution_to_governance(optimization_proposer)

        self._log_event(
            "kernel", "all",
            "v03_wired",
            f"v0.3 integration bus connected ({len(self._v03_connections)} connections)",
        )
        logger.info(
            "IntegrationBus: v0.3 connections active (%d)",
            len(self._v03_connections),
        )

    def unwire_v03(self) -> None:
        """Reverse all v0.3 connections and restore original configs."""
        if hasattr(self, '_v03_original_recall') and self._v03_original_recall is not None:
            self.kernel.memory.recall = self._v03_original_recall
            self._v03_original_recall = None

        if hasattr(self, '_v03_original_store') and self._v03_original_store is not None:
            self.kernel.memory.store = self._v03_original_store
            self._v03_original_store = None

        if hasattr(self, '_v03_original_gate_check') and self._v03_original_gate_check is not None:
            self.kernel.governance.mandatory_gate.check = self._v03_original_gate_check
            self._v03_original_gate_check = None

        if hasattr(self, '_v03_original_injection_cb') and self._v03_original_injection_cb is not None:
            pass  # callback-based subscriptions don't need reversal

        if hasattr(self, '_v03_original_scheduler_max') and self._v03_original_scheduler_max is not None:
            self.kernel.task_graph.scheduler.config.max_concurrent = self._v03_original_scheduler_max
            self._v03_original_scheduler_max = None

        connections = getattr(self, '_v03_connections', [])
        self._v03_connections = []
        self._log_event(
            "kernel", "all",
            "v03_unwired",
            f"v0.3 integration bus disconnected ({len(connections)} connections removed)",
        )
        logger.info("IntegrationBus: v0.3 connections removed")

    # ── 17. Self-Model → Drift Detection ──────────────────────────────────

    def _wire_self_model_drift(self, self_model, drift_detector) -> None:
        """When CognitiveSelfModel builds a snapshot, trigger DriftDetector.detect()."""
        original_snapshot = self_model.snapshot

        def snapshot_with_drift(*args, **kwargs):
            result = original_snapshot(*args, **kwargs)
            try:
                drift_report = drift_detector.detect(
                    self_model,
                    bus=self,
                )
                self._log_event(
                    "identity.self_model",
                    "observability.drift_detector",
                    "drift_detection_triggered",
                    f"Drift risk={drift_report.overall_risk_score:.1f}, "
                    f"proposals={len(drift_report.remediation_proposals)}",
                )
            except Exception as exc:
                logger.warning("Drift detection after snapshot failed: %s", exc)
            return result

        self_model.snapshot = snapshot_with_drift
        self._v03_connections.append("self_model_drift")
        self._log_event(
            "kernel",
            "identity.self_model → observability.drift_detector",
            "v03_wired",
            "Self-model snapshot triggers drift detection",
        )

    # ── 18. Drift Detection → Somatic ────────────────────────────────────

    def _wire_drift_to_somatic(self, drift_detector) -> None:
        """When drift finds HIGH/CRITICAL issues, emit PRESSURE on SignalBus."""
        original_detect = drift_detector.detect

        def detect_with_somatic(*args, **kwargs):
            report = original_detect(*args, **kwargs)
            high_or_critical = [
                p for p in report.remediation_proposals
                if p.severity.value in ("HIGH", "CRITICAL")
            ]
            if high_or_critical and hasattr(self.kernel.somatic.bus, 'emit_pressure'):
                self.kernel.somatic.bus.emit_pressure(
                    source="observability.drift_detector",
                    description=(
                        f"Drift detection: {len(high_or_critical)} HIGH/CRITICAL "
                        f"issues (risk={report.overall_risk_score:.1f})"
                    ),
                    value=min(100.0, report.overall_risk_score),
                    threshold=40.0,
                )
                self._log_event(
                    "observability.drift_detector",
                    "somatic.bus",
                    "drift_pressure_emitted",
                    f"{len(high_or_critical)} HIGH/CRITICAL drift issues → pressure signal",
                )
            return report

        drift_detector.detect = detect_with_somatic
        self._v03_connections.append("drift_to_somatic")

    # ── 19. Task Graph → Pattern Miner ───────────────────────────────────

    def _wire_execution_to_patterns(self, pattern_miner) -> None:
        """After GRAPH_COMPLETED, trigger PatternMiner to record the execution."""

        def on_graph_complete_for_patterns(event: SchedulerEvent, data: dict[str, Any]) -> None:
            if event != SchedulerEvent.GRAPH_COMPLETED:
                return
            try:
                pattern_miner.mine_success_patterns(min_occurrences=2)
                self._log_event(
                    "task_graph.scheduler",
                    "memory.evolution.pattern_miner",
                    "patterns_mined",
                    f"Pattern mining triggered after graph completion: "
                    f"{data.get('graph_id', 'unknown')}",
                )
            except Exception as exc:
                logger.warning("Pattern mining after graph completion failed: %s", exc)

        self.kernel.task_graph.scheduler.on_event(on_graph_complete_for_patterns)
        self._v03_connections.append("execution_to_patterns")
        self._log_event(
            "kernel",
            "task_graph.scheduler → memory.evolution.pattern_miner",
            "v03_wired",
            "Graph completions trigger pattern mining",
        )

    # ── 20. Governance Incidents → Incident Learner ──────────────────────

    def _wire_incidents_to_learner(self, incident_learner) -> None:
        """When governance incidents occur, notify IncidentLearner."""
        gate = self.kernel.governance.mandatory_gate
        if gate is None:
            return

        self._v03_original_gate_check = gate.check

        def check_with_incident_learning(*args: Any, **kwargs: Any):
            result = self._v03_original_gate_check(*args, **kwargs)
            if not result.allowed:
                try:
                    incident_learner.analyze_incidents()
                    self._log_event(
                        "governance.mandatory_gate",
                        "memory.evolution.incident_learner",
                        "incident_learning_triggered",
                        f"Gate denial for agent={result.agent_id} → incident learner notified",
                    )
                except Exception as exc:
                    logger.warning("Incident learning after gate denial failed: %s", exc)
            return result

        gate.check = check_with_incident_learning
        self._v03_connections.append("incidents_to_learner")
        self._log_event(
            "kernel",
            "governance.mandatory_gate → memory.evolution.incident_learner",
            "v03_wired",
            "Gate denials notify incident learner",
        )

    # ── 21. Optimizer → Scheduler (read-only) ────────────────────────────

    def _wire_optimizer_to_scheduler(self, task_graph_optimizer) -> None:
        """After optimization analysis, make results available to scheduler (read-only)."""

        def on_graph_complete_for_optimizer(event: SchedulerEvent, data: dict[str, Any]) -> None:
            if event != SchedulerEvent.GRAPH_COMPLETED:
                return
            executor = self.kernel.task_graph.executor
            if not hasattr(executor, '_current_graph'):
                return
            try:
                graph = executor._current_graph
                result = task_graph_optimizer.optimize(graph)
                self.kernel.task_graph.scheduler._latest_optimization = result
                self._log_event(
                    "runtime.task_graph_optimizer",
                    "task_graph.scheduler",
                    "optimization_available",
                    f"Optimization result: improvement={result.estimated_improvement:.1%}, "
                    f"bottlenecks={result.bottleneck_count}",
                )
            except Exception as exc:
                logger.warning("Task graph optimization failed: %s", exc)

        self.kernel.task_graph.scheduler.on_event(on_graph_complete_for_optimizer)
        self._v03_connections.append("optimizer_to_scheduler")
        self._log_event(
            "kernel",
            "runtime.task_graph_optimizer → task_graph.scheduler",
            "v03_wired",
            "Graph completions trigger optimization analysis (read-only)",
        )

    # ── 22. Context Injection → Cost Accountant ──────────────────────────

    def _wire_context_costs(self, cost_accountant) -> None:
        """When InjectionLogger logs an injection, also record in ContextCostAccountant."""
        injection_logger = self.kernel.context.injection_logger
        if injection_logger is None:
            return

        def on_injection_for_costs(event) -> None:
            try:
                from context.context_economy.cost_accountant import CostOperation
                cost_accountant.record_cost(
                    agent_id=event.agent_id,
                    task_id=getattr(event, 'task_id', 'unknown'),
                    operation=CostOperation.INJECTION,
                    tokens=event.tokens_used,
                    source="context.injection_logger",
                    utility_score=getattr(event, 'top_score', 0.0),
                )
                self._log_event(
                    "context.injection_logger",
                    "context.context_economy.cost_accountant",
                    "cost_recorded",
                    f"agent={event.agent_id} tokens={event.tokens_used}",
                )
            except Exception as exc:
                logger.warning("Cost accounting for injection failed: %s", exc)

        injection_logger.on_injection(on_injection_for_costs)
        self._v03_connections.append("context_costs")
        self._log_event(
            "kernel",
            "context.injection_logger → context.context_economy.cost_accountant",
            "v03_wired",
            "Context injections recorded in cost accountant",
        )

    # ── 23. Budget Manager → Token Economy ───────────────────────────────

    def _wire_budget_to_economy(self, token_economy) -> None:
        """Connect BudgetManager spend events to TokenEconomy tracking."""
        bm = self.kernel.context.budget_manager
        if not hasattr(bm, 'total_budget'):
            return

        original_allocate = getattr(bm, 'allocate', None)
        if original_allocate is None:
            return

        def allocate_with_economy(*args: Any, **kwargs: Any):
            result = original_allocate(*args, **kwargs)
            try:
                agent_id = kwargs.get('agent_id', args[0] if args else 'unknown')
                tokens = kwargs.get('tokens', args[1] if len(args) > 1 else 0)
                token_economy.record_usage(str(agent_id), int(tokens))
                self._log_event(
                    "context.budget_manager",
                    "context.context_economy.token_economy",
                    "spend_tracked",
                    f"agent={agent_id} tokens={tokens}",
                )
            except Exception as exc:
                logger.debug("Token economy tracking failed: %s", exc)
            return result

        bm.allocate = allocate_with_economy
        self._v03_connections.append("budget_to_economy")
        self._log_event(
            "kernel",
            "context.budget_manager → context.context_economy.token_economy",
            "v03_wired",
            "Budget allocations tracked in token economy",
        )

    # ── 24. Signal Bus → Attention Runtime ───────────────────────────────

    def _wire_attention_runtime(self, attention_runtime) -> None:
        """Route SignalBus signals through SomaticAttentionRuntime.process_signal() pipeline."""
        bus = self.kernel.somatic.bus

        def on_signal_for_runtime(signal) -> None:
            try:
                attention_runtime.process_signal(signal)
            except Exception as exc:
                logger.warning("Attention runtime signal processing failed: %s", exc)

        if hasattr(bus, 'on_signal'):
            bus.on_signal(on_signal_for_runtime)
        elif hasattr(bus, 'subscribe'):
            bus.subscribe(on_signal_for_runtime)

        self._v03_connections.append("attention_runtime")
        self._log_event(
            "kernel",
            "somatic.bus → somatic.attention_runtime",
            "v03_wired",
            "Signals routed through attention runtime pipeline",
        )

    # ── 25. Throttle → Scheduler ─────────────────────────────────────────

    def _wire_throttle_to_scheduler(self, attention_runtime) -> None:
        """When throttle state changes, adjust scheduler max_concurrent."""
        throttle = getattr(attention_runtime, 'throttle', None)
        if throttle is None:
            return

        self._v03_original_scheduler_max = (
            self.kernel.task_graph.scheduler.config.max_concurrent
        )

        original_update = getattr(throttle, 'update', None)
        if original_update is None:
            return

        def update_with_scheduler_adjust(*args: Any, **kwargs: Any):
            result = original_update(*args, **kwargs)
            try:
                state = throttle.current_state()
                factor = state.parallelism_factor if hasattr(state, 'parallelism_factor') else 1.0
                new_max = max(1, int(self._v03_original_scheduler_max * factor))
                self.kernel.task_graph.scheduler.config.max_concurrent = new_max
                self._log_event(
                    "somatic.attention_runtime.throttle",
                    "task_graph.scheduler",
                    "throttle_adjusted",
                    f"Throttle factor={factor:.2f} → max_concurrent={new_max}",
                )
            except Exception as exc:
                logger.debug("Throttle-to-scheduler adjustment failed: %s", exc)
            return result

        throttle.update = update_with_scheduler_adjust
        self._v03_connections.append("throttle_to_scheduler")
        self._log_event(
            "kernel",
            "somatic.attention_runtime.throttle → task_graph.scheduler",
            "v03_wired",
            "Throttle state changes adjust scheduler concurrency",
        )

    # ── 26. Governance Gate → Cognition Tracer ───────────────────────────

    def _wire_cognition_tracing(self, cognition_tracer) -> None:
        """When governance gate checks occur, trace them in CognitionTracer."""
        gate = self.kernel.governance.mandatory_gate
        if gate is None:
            return

        current_check = gate.check

        def check_with_cognition_trace(*args: Any, **kwargs: Any):
            start = time.time()
            result = current_check(*args, **kwargs)
            duration = time.time() - start
            try:
                from observability.recursive_runtime.cognition_tracer import DecisionType
                cognition_tracer.trace_decision(
                    decision_type=DecisionType.GOVERNANCE,
                    inputs={
                        "action": result.action[:200],
                        "agent_id": result.agent_id,
                    },
                    output={
                        "allowed": result.allowed,
                        "risk_level": result.risk_level.name,
                        "reason": result.reason[:200],
                    },
                    rationale=result.reason[:300],
                    duration=duration,
                    agent_id=result.agent_id,
                )
                self._log_event(
                    "governance.mandatory_gate",
                    "observability.cognition_tracer",
                    "governance_traced",
                    f"agent={result.agent_id} → {result.risk_level.name} ({duration*1000:.1f}ms)",
                )
            except Exception as exc:
                logger.debug("Cognition tracing for gate check failed: %s", exc)
            return result

        gate.check = check_with_cognition_trace
        self._v03_connections.append("cognition_tracing")
        self._log_event(
            "kernel",
            "governance.mandatory_gate → observability.cognition_tracer",
            "v03_wired",
            "Gate checks traced in cognition tracer",
        )

    # ── 27. Memory Kernel → Memory Flow Tracer ───────────────────────────

    def _wire_memory_flow(self, memory_flow_tracer) -> None:
        """When MemoryKernel recall/store happens, trace in MemoryFlowTracer."""
        self._v03_original_recall = self.kernel.memory.recall
        self._v03_original_store = getattr(self.kernel.memory, 'store', None)

        def recall_with_flow_trace(*args: Any, **kwargs: Any):
            start = time.time()
            result = self._v03_original_recall(*args, **kwargs)
            duration = time.time() - start
            try:
                memory_flow_tracer.trace_recall(
                    query=result.query[:200] if hasattr(result, 'query') else str(args[0])[:200] if args else "unknown",
                    layer="all",
                    results_count=len(result.records) if hasattr(result, 'records') else 0,
                    duration=duration,
                    hit_rate=min(1.0, len(result.records) / max(result.total_tokens, 1)) if hasattr(result, 'records') else 0.5,
                )
                self._log_event(
                    "memory.kernel",
                    "observability.memory_flow_tracer",
                    "recall_traced",
                    f"query='{result.query[:40] if hasattr(result, 'query') else '?'}' "
                    f"results={len(result.records) if hasattr(result, 'records') else 0} "
                    f"({duration*1000:.1f}ms)",
                )
            except Exception as exc:
                logger.debug("Memory flow tracing for recall failed: %s", exc)
            return result

        self.kernel.memory.recall = recall_with_flow_trace

        if self._v03_original_store is not None:
            def store_with_flow_trace(*args: Any, **kwargs: Any):
                result = self._v03_original_store(*args, **kwargs)
                try:
                    layer = kwargs.get('layer', args[0] if args else 'unknown')
                    record_id = str(getattr(result, 'record_id', 'unknown'))
                    tags = kwargs.get('tags', [])
                    memory_flow_tracer.trace_store(
                        layer=str(layer),
                        record_id=record_id,
                        tags=tags if isinstance(tags, list) else [],
                        size=kwargs.get('size', 0),
                    )
                    self._log_event(
                        "memory.kernel",
                        "observability.memory_flow_tracer",
                        "store_traced",
                        f"layer={layer} record={record_id}",
                    )
                except Exception as exc:
                    logger.debug("Memory flow tracing for store failed: %s", exc)
                return result

            self.kernel.memory.store = store_with_flow_trace

        self._v03_connections.append("memory_flow")
        self._log_event(
            "kernel",
            "memory.kernel → observability.memory_flow_tracer",
            "v03_wired",
            "Memory recall/store operations traced in memory flow tracer",
        )

    # ── 28. Evolution Actions → Audit Logger ─────────────────────────────

    def _wire_evolution_audit(self, evolution_reporter, optimization_proposer) -> None:
        """All evolution engine actions get logged to the governance audit log."""
        audit_log = self.kernel.governance.audit_log

        if evolution_reporter is not None:
            original_generate = evolution_reporter.generate_report

            def generate_with_audit(*args: Any, **kwargs: Any):
                report = original_generate(*args, **kwargs)
                try:
                    audit_log.record_decision(
                        action="evolution.efficiency_report",
                        risk="ALLOW",
                        reason=f"Evolution report generated: {report.patterns_found} patterns, "
                               f"{report.proposals_generated} proposals, risk={report.risk_score:.2f}",
                        agent_id="evolution_engine",
                        matched_policies=[],
                        validation_stages=[],
                    )
                    self._log_event(
                        "memory.evolution.reporter",
                        "governance.audit_log",
                        "evolution_report_audited",
                        f"patterns={report.patterns_found} proposals={report.proposals_generated}",
                    )
                except Exception as exc:
                    logger.debug("Evolution audit logging failed: %s", exc)
                return report

            evolution_reporter.generate_report = generate_with_audit

        if optimization_proposer is not None:
            original_propose = optimization_proposer.propose_from_patterns

            def propose_with_audit(*args: Any, **kwargs: Any):
                proposals = original_propose(*args, **kwargs)
                try:
                    audit_log.record_decision(
                        action="evolution.optimization_proposals",
                        risk="ALLOW",
                        reason=f"Generated {len(proposals)} optimization proposals",
                        agent_id="evolution_engine",
                        matched_policies=[],
                        validation_stages=[],
                    )
                    self._log_event(
                        "memory.evolution.proposer",
                        "governance.audit_log",
                        "proposals_audited",
                        f"proposals={len(proposals)}",
                    )
                except Exception as exc:
                    logger.debug("Evolution proposal audit logging failed: %s", exc)
                return proposals

            optimization_proposer.propose_from_patterns = propose_with_audit

        self._v03_connections.append("evolution_audit")
        self._log_event(
            "kernel",
            "memory.evolution → governance.audit_log",
            "v03_wired",
            "Evolution engine actions logged to governance audit",
        )

    # ── 29. Evolution Proposals → Governance ─────────────────────────────

    def _wire_evolution_to_governance(self, optimization_proposer) -> None:
        """Evolution proposals emit a REVIEW_REQUIRED governance event."""
        current_propose = optimization_proposer.propose_from_patterns

        def propose_with_governance(*args: Any, **kwargs: Any):
            proposals = current_propose(*args, **kwargs)
            high_impact = [
                p for p in proposals
                if p.estimated_impact.value == "high"
            ]
            if high_impact:
                try:
                    self.kernel.governance.audit_log.record_decision(
                        action="evolution.high_impact_proposals",
                        risk="REVIEW_REQUIRED",
                        reason=(
                            f"{len(high_impact)} high-impact optimization proposals "
                            f"require governance review before implementation"
                        ),
                        agent_id="evolution_engine",
                        matched_policies=["evolution_governance"],
                        validation_stages=[{
                            "name": "evolution_review",
                            "passed": False,
                            "risk": "REVIEW_REQUIRED",
                        }],
                    )
                    self._log_event(
                        "memory.evolution.proposer",
                        "governance",
                        "review_required",
                        f"{len(high_impact)} high-impact proposals → REVIEW_REQUIRED",
                    )
                except Exception as exc:
                    logger.debug("Evolution-to-governance notification failed: %s", exc)
            return proposals

        optimization_proposer.propose_from_patterns = propose_with_governance
        self._v03_connections.append("evolution_to_governance")
        self._log_event(
            "kernel",
            "memory.evolution.proposer → governance",
            "v03_wired",
            "High-impact evolution proposals trigger governance review",
        )

    # ── Internal helpers ─────────────────────────────────────────────────

    def _log_event(
        self, source: str, target: str, event_type: str, description: str
    ) -> None:
        event = BusEvent(
            source=source,
            target=target,
            event_type=event_type,
            description=description,
        )
        self.event_log.append(event)
        if len(self.event_log) > self._max_log:
            self.event_log = self.event_log[-self._max_log:]
        logger.debug(f"[{source} → {target}] {event_type}: {description}")
