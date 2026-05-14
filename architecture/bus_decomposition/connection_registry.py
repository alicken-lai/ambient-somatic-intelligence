"""Connection lifecycle registry for IntegrationBus.

Tracks wire/unwire state of every connection and provides runtime
introspection: which connections are active, which subsystems are
coupled, and whether the bus is healthy.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class ConnectionRecord:
    name: str
    source: str
    target: str
    mechanism: str
    version: str
    wired_at: str | None = None
    unwired_at: str | None = None
    is_active: bool = False
    stack_depth: int = 0
    original_method: str | None = None
    notes: str = ""


@dataclass
class RegistryHealthReport:
    total_expected: int
    total_active: int
    missing: list[str] = field(default_factory=list)
    extra: list[str] = field(default_factory=list)
    stale: list[str] = field(default_factory=list)
    is_healthy: bool = True
    checked_at: str = ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_V02_CONNECTIONS: list[dict[str, str | int]] = [
    {"name": "somatic_to_scheduler", "source": "somatic.attention", "target": "task_graph.scheduler", "mechanism": "callback", "stack_depth": 0, "original_method": "AttentionManager.on_change", "notes": "Adjusts scheduler concurrency on attention change"},
    {"name": "somatic_to_context", "source": "somatic.attention", "target": "context.budget_manager", "mechanism": "callback", "stack_depth": 0, "original_method": "AttentionManager.on_change", "notes": "Scales context token budget under stress"},
    {"name": "attention_to_governance", "source": "somatic.attention", "target": "governance", "mechanism": "callback", "stack_depth": 0, "original_method": "AttentionManager.on_change", "notes": "Logs governance sensitivity changes"},
    {"name": "governance_to_audit", "source": "governance.validator", "target": "governance.audit_log", "mechanism": "monkey_patch", "stack_depth": 1, "original_method": "validator.validate", "notes": "Records every validation decision"},
    {"name": "tasks_to_tracer", "source": "task_graph.scheduler", "target": "observability.tracer", "mechanism": "callback", "stack_depth": 0, "original_method": "Scheduler.on_event", "notes": "Traces scheduler events into observability"},
    {"name": "attention_to_agents", "source": "somatic.attention", "target": "agent_runtime", "mechanism": "callback", "stack_depth": 0, "original_method": "AttentionManager.on_change", "notes": "Caps agent parallelism when stressed"},
    {"name": "memory_metrics", "source": "memory.kernel", "target": "observability.metrics", "mechanism": "monkey_patch", "stack_depth": 1, "original_method": "memory.recall", "notes": "Tracks recall operations in metrics"},
    {"name": "injection_to_tracer", "source": "context.injection_logger", "target": "observability.tracer", "mechanism": "callback", "stack_depth": 0, "original_method": "InjectionLogger.on_injection", "notes": "Traces context injections and increments metrics"},
    {"name": "failure_propagation", "source": "task_graph.scheduler", "target": "task_graph.failure_propagator", "mechanism": "callback", "stack_depth": 0, "original_method": "Scheduler.on_event", "notes": "Propagates task failures through DAG"},
    {"name": "checkpoint_cleanup", "source": "task_graph.scheduler", "target": "task_graph.checkpoint", "mechanism": "callback", "stack_depth": 0, "original_method": "Scheduler.on_event", "notes": "Auto-cleans old checkpoints after graph completion"},
    {"name": "mandatory_gate_audit", "source": "governance.mandatory_gate", "target": "observability.tracer", "mechanism": "monkey_patch", "stack_depth": 1, "original_method": "gate.check", "notes": "First layer in gate.check patch chain"},
    {"name": "tool_permission_somatic", "source": "governance.tool_permissions", "target": "somatic.bus", "mechanism": "monkey_patch", "stack_depth": 2, "original_method": "gate.check", "notes": "Stacks on mandatory_gate_audit; emits pain on denial"},
    {"name": "signal_correlator", "source": "somatic.correlator", "target": "observability.tracer", "mechanism": "callback", "stack_depth": 0, "original_method": "SignalCorrelator.on_correlation", "notes": "Forwards correlation events to tracer"},
    {"name": "rate_tracker", "source": "somatic.bus", "target": "somatic.rate_tracker", "mechanism": "callback", "stack_depth": 0, "original_method": "RateTracker.subscribe", "notes": "Subscription-only; tracker self-subscribes to bus"},
    {"name": "analytics_to_health", "source": "somatic.analytics", "target": "kernel.health", "mechanism": "monkey_patch", "stack_depth": 1, "original_method": "kernel.health", "notes": "Merges somatic health into kernel.health()"},
    {"name": "agent_decision_log", "source": "observability.telemetry", "target": "observability.decision_log", "mechanism": "monkey_patch", "stack_depth": 1, "original_method": "telemetry.complete_task", "notes": "Logs task completions as decisions"},
]

_V03_CONNECTIONS: list[dict[str, str | int]] = [
    {"name": "self_model_drift", "source": "identity.self_model", "target": "observability.drift_detector", "mechanism": "monkey_patch", "stack_depth": 1, "original_method": "self_model.snapshot", "notes": "Triggers drift detection on snapshot"},
    {"name": "drift_to_somatic", "source": "observability.drift_detector", "target": "somatic.bus", "mechanism": "monkey_patch", "stack_depth": 1, "original_method": "drift_detector.detect", "notes": "Emits pressure on HIGH/CRITICAL drift"},
    {"name": "execution_to_patterns", "source": "task_graph.scheduler", "target": "memory.evolution.pattern_miner", "mechanism": "callback", "stack_depth": 0, "original_method": "Scheduler.on_event", "notes": "Triggers pattern mining after graph completion"},
    {"name": "incidents_to_learner", "source": "governance.mandatory_gate", "target": "memory.evolution.incident_learner", "mechanism": "monkey_patch", "stack_depth": 3, "original_method": "gate.check", "notes": "Stacks on v0.2 gate patches; notifies on denial"},
    {"name": "optimizer_to_scheduler", "source": "runtime.task_graph_optimizer", "target": "task_graph.scheduler", "mechanism": "callback", "stack_depth": 0, "original_method": "Scheduler.on_event", "notes": "Stores optimization result on scheduler (read-only)"},
    {"name": "context_costs", "source": "context.injection_logger", "target": "context.context_economy.cost_accountant", "mechanism": "callback", "stack_depth": 0, "original_method": "InjectionLogger.on_injection", "notes": "Records injection costs in cost accountant"},
    {"name": "budget_to_economy", "source": "context.budget_manager", "target": "context.context_economy.token_economy", "mechanism": "monkey_patch", "stack_depth": 1, "original_method": "budget_manager.allocate", "notes": "Tracks allocations in token economy"},
    {"name": "attention_runtime", "source": "somatic.bus", "target": "somatic.attention_runtime", "mechanism": "callback", "stack_depth": 0, "original_method": "SomaticSignalBus.on_signal", "notes": "Forwards all signals to attention runtime"},
    {"name": "throttle_to_scheduler", "source": "somatic.attention_runtime.throttle", "target": "task_graph.scheduler", "mechanism": "monkey_patch", "stack_depth": 1, "original_method": "throttle.update", "notes": "Adjusts scheduler concurrency on throttle change"},
    {"name": "cognition_tracing", "source": "governance.mandatory_gate", "target": "observability.cognition_tracer", "mechanism": "monkey_patch", "stack_depth": 4, "original_method": "gate.check", "notes": "Stacks on all prior gate patches; traces in cognition tracer"},
    {"name": "memory_flow", "source": "memory.kernel", "target": "observability.memory_flow_tracer", "mechanism": "monkey_patch", "stack_depth": 2, "original_method": "memory.recall + memory.store", "notes": "Stacks on v0.2 memory_metrics for recall; also patches store"},
    {"name": "evolution_audit", "source": "memory.evolution", "target": "governance.audit_log", "mechanism": "monkey_patch", "stack_depth": 1, "original_method": "reporter.generate_report + proposer.propose_from_patterns", "notes": "Logs all evolution actions to governance audit"},
    {"name": "evolution_to_governance", "source": "memory.evolution.proposer", "target": "governance", "mechanism": "monkey_patch", "stack_depth": 2, "original_method": "proposer.propose_from_patterns", "notes": "Stacks on evolution_audit; emits REVIEW_REQUIRED for high-impact"},
]


class ConnectionRegistry:
    """Tracks the lifecycle of all IntegrationBus connections."""

    def __init__(self) -> None:
        self._connections: dict[str, ConnectionRecord] = {}
        self._expected: set[str] = set()
        self._populate_expected()
        logger.debug("ConnectionRegistry initialized with %d expected connections", len(self._expected))

    def _populate_expected(self) -> None:
        for spec in _V02_CONNECTIONS + _V03_CONNECTIONS:
            record = ConnectionRecord(
                name=str(spec["name"]),
                source=str(spec["source"]),
                target=str(spec["target"]),
                mechanism=str(spec["mechanism"]),
                version="v0.2" if spec in _V02_CONNECTIONS else "v0.3",
                stack_depth=int(spec["stack_depth"]),
                original_method=str(spec.get("original_method", "")),
                notes=str(spec.get("notes", "")),
            )
            self._connections[record.name] = record
            self._expected.add(record.name)

    def register_connection(self, conn: ConnectionRecord) -> None:
        conn.wired_at = conn.wired_at or _now_iso()
        conn.is_active = True
        self._connections[conn.name] = conn
        logger.debug("Registered connection: %s", conn.name)

    def unregister_connection(self, name: str) -> bool:
        record = self._connections.get(name)
        if record is None:
            return False
        record.is_active = False
        record.unwired_at = _now_iso()
        return True

    def get_connection(self, name: str) -> ConnectionRecord | None:
        return self._connections.get(name)

    def get_active_connections(self) -> list[ConnectionRecord]:
        return [c for c in self._connections.values() if c.is_active]

    def get_connections_by_subsystem(self, subsystem: str) -> list[ConnectionRecord]:
        return [
            c for c in self._connections.values()
            if subsystem in c.source or subsystem in c.target
        ]

    def get_monkey_patches(self) -> list[ConnectionRecord]:
        return [c for c in self._connections.values() if c.mechanism == "monkey_patch"]

    def get_callbacks(self) -> list[ConnectionRecord]:
        return [c for c in self._connections.values() if c.mechanism == "callback"]

    def check_health(self) -> RegistryHealthReport:
        active_names = {c.name for c in self._connections.values() if c.is_active}
        all_names = set(self._connections.keys())
        missing = sorted(self._expected - active_names)
        extra = sorted(active_names - self._expected)
        stale = sorted(
            c.name for c in self._connections.values()
            if c.unwired_at is not None and c.is_active
        )
        is_healthy = len(missing) == 0 and len(extra) == 0 and len(stale) == 0
        return RegistryHealthReport(
            total_expected=len(self._expected),
            total_active=len(active_names),
            missing=missing,
            extra=extra,
            stale=stale,
            is_healthy=is_healthy,
            checked_at=_now_iso(),
        )

    def get_dependency_matrix(self) -> dict[str, list[str]]:
        matrix: dict[str, set[str]] = {}
        for conn in self._connections.values():
            source_base = conn.source.split(".")[0]
            target_base = conn.target.split(".")[0]
            if source_base not in matrix:
                matrix[source_base] = set()
            matrix[source_base].add(target_base)
        return {k: sorted(v) for k, v in sorted(matrix.items())}
