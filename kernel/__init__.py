"""
Ambient OS Cognitive Runtime Kernel — Unified API entry point.

The kernel provides a single integration surface for all 6 core subsystems:

  1. memory-kernel    — 6-layer governed memory (episodic/semantic/procedural/governance/scratchpad/archive)
  2. context-engine   — Token-budgeted context assembly with semantic retrieval and compression
  3. task-graph-engine — DAG-based task scheduling with checkpoint/rollback
  4. governance-kernel — Policy engine, execution validation, anomaly detection, audit
  5. agent-runtime    — Persistent specialized agents with local memory and orchestration
  6. somatic-signal-bus — Environmental cognition via signal bus, attention, and anomaly response

Usage:
    from kernel import AmbientKernel

    k = AmbientKernel.boot()
    k.somatic.bus.emit_pressure("memory", "Memory at 92%", 92.0, 85.0)
    result = k.governance.validator.validate("git push", agent_id="cursor")
    context = k.context.assembler.assemble("fix login bug", agent_id="frontend-agent")
"""

from __future__ import annotations

__version__ = "0.4.1-alpha"
__all__ = [
    "AmbientKernel",
    "get_memory_kernel",
    "memory",
    "context",
    "task_graph",
    "governance",
    "agents",
    "somatic",
    "observability",
]

_memory_kernel_instance = None


def get_memory_kernel():
    """Return the canonical MemoryKernel singleton (shared with AmbientKernel.memory)."""
    global _memory_kernel_instance
    if _memory_kernel_instance is None:
        from memory.memory_kernel import MemoryKernel
        _memory_kernel_instance = MemoryKernel()
    return _memory_kernel_instance


class _MemoryKernelProxy:
    """Module-level binding to the same MemoryKernel instance as AmbientKernel.memory."""

    def __getattr__(self, name: str):
        return getattr(get_memory_kernel(), name)

    def __repr__(self) -> str:
        return f"<kernel.memory proxy for {get_memory_kernel()!r}>"


memory = _MemoryKernelProxy()


class _SubsystemRef:
    """Lazy reference to a subsystem — avoids import-time coupling."""

    def __init__(self, module_path: str):
        self._module_path = module_path
        self._module = None

    def __getattr__(self, name: str):
        if self._module is None:
            import importlib
            self._module = importlib.import_module(self._module_path)
        return getattr(self._module, name)


context = _SubsystemRef("context")
task_graph = _SubsystemRef("runtime.task_graph")
governance = _SubsystemRef("governance")
agents = _SubsystemRef("agents")
somatic = _SubsystemRef("somatic")
observability = _SubsystemRef("observability")


class AmbientKernel:
    """
    The unified cognitive runtime kernel.

    Holds references to all initialized subsystem instances and the integration
    bus that wires them together. Use AmbientKernel.boot() to create a fully
    wired kernel, or instantiate manually for testing.
    """

    def __init__(self):
        from somatic.signal_bus import SomaticSignalBus  # noqa: local import
        from somatic.attention_manager import AttentionManager
        from somatic.environment_monitor import EnvironmentMonitor
        from somatic.anomaly_event_stream import AnomalyEventStream
        from somatic.signal_normalizer import SignalNormalizer
        from somatic.signal_correlator import SignalCorrelator
        from somatic.rate_tracker import RateTracker
        from somatic.signal_analytics import SignalAnalytics
        from governance.policy_engine import PolicyEngine
        from governance.execution_validator import ExecutionValidator
        from governance.anomaly_detector import AnomalyDetector
        from governance.audit_log import GovernanceAuditLog
        from governance.tool_permissions import ToolPermissionMatrix
        from governance.mandatory_gate import MandatoryGate
        from governance.unified_router import UnifiedRouter
        from context.assembler import ContextAssembler
        from context.budget_manager import ContextBudgetManager
        from context.memory_compressor import MemoryCompressor
        from context.injection_logger import InjectionLogger
        from context.kernel_retriever import KernelRetriever
        from runtime.task_graph.executor import TaskExecutor
        from agents.registry import AgentRegistry
        from agents.orchestrator import AgentOrchestrator
        from agents.isolation import AgentIsolationManager
        from observability.tracer import ExecutionTracer
        from observability.metrics_collector import MetricsCollector
        from observability.telemetry import AgentTelemetry
        from observability.dashboard import Dashboard
        from observability.agent_decision_log import AgentDecisionLog
        from observability.system_report import SystemReport
        from observability.trace_schema import TraceEventSchema

        self.somatic = _SomaticSubsystem(
            bus=SomaticSignalBus(),
            attention=None,
            monitor=None,
            anomaly_stream=None,
        )
        self.somatic.attention = AttentionManager(self.somatic.bus)
        self.somatic.monitor = EnvironmentMonitor(self.somatic.bus)
        self.somatic.anomaly_stream = AnomalyEventStream(self.somatic.bus)
        self.somatic.normalizer = SignalNormalizer()
        self.somatic.correlator = SignalCorrelator(self.somatic.bus)
        self.somatic.rate_tracker = RateTracker(self.somatic.bus)
        self.somatic.analytics = SignalAnalytics(self.somatic.bus)

        policy_engine = PolicyEngine()
        anomaly_detector = AnomalyDetector()
        audit_log = GovernanceAuditLog()
        validator = ExecutionValidator(policy_engine, anomaly_detector)
        tool_permissions = ToolPermissionMatrix()
        mandatory_gate = MandatoryGate(validator, tool_permissions, audit_log)
        unified_router = UnifiedRouter(mandatory_gate, legacy_policy_engine=policy_engine)

        self.governance = _GovernanceSubsystem(
            policy_engine=policy_engine,
            validator=validator,
            anomaly_detector=anomaly_detector,
            audit_log=audit_log,
        )
        self.governance.tool_permissions = tool_permissions
        self.governance.mandatory_gate = mandatory_gate
        self.governance.unified_router = unified_router

        self.memory = get_memory_kernel()

        injection_logger = InjectionLogger()
        kernel_retriever = KernelRetriever(self.memory)

        self.context = _ContextSubsystem(
            budget_manager=ContextBudgetManager(),
            retriever=kernel_retriever,
            kernel_retriever=kernel_retriever,
            compressor=MemoryCompressor(),
            assembler=ContextAssembler(retriever=kernel_retriever),
            injection_logger=injection_logger,
        )

        from runtime.task_graph.visualizer import DAGVisualizer

        executor = TaskExecutor()
        self.task_graph = _TaskGraphSubsystem(
            scheduler=executor.scheduler,
            checkpoint=executor.checkpoint_mgr,
            executor=executor,
        )
        self.task_graph.visualizer = DAGVisualizer()

        registry = AgentRegistry()
        isolation_manager = AgentIsolationManager(self.memory)
        self.agents = _AgentSubsystem(
            registry=registry,
            orchestrator=AgentOrchestrator(registry),
            isolation_manager=isolation_manager,
        )

        metrics = MetricsCollector()
        tracer = ExecutionTracer()
        telemetry = AgentTelemetry(metrics)
        decision_log = AgentDecisionLog()
        trace_schema = TraceEventSchema()
        dashboard = Dashboard(
            metrics, telemetry, tracer,
            dag_visualizer=self.task_graph.visualizer,
            signal_analytics=self.somatic.analytics,
            memory_kernel=self.memory,
        )
        self.observability = _ObservabilitySubsystem(
            tracer=tracer,
            metrics=metrics,
            telemetry=telemetry,
            dashboard=dashboard,
        )
        self.observability.decision_log = decision_log
        self.observability.trace_schema = trace_schema

        self._integration_bus = None
        self._v03: "_V03Subsystems | None" = None

    @classmethod
    def boot(cls) -> "AmbientKernel":
        """Create a fully wired kernel with integration bus active."""
        from kernel.integration_bus import IntegrationBus
        from observability.system_report import SystemReport

        k = cls()
        k._integration_bus = IntegrationBus(k)
        k._integration_bus.wire()
        k.observability.system_report = SystemReport(k)
        return k

    @property
    def integration_bus(self):
        return self._integration_bus

    @property
    def v03(self) -> "_V03Subsystems | None":
        """Access v0.3 subsystems (None if v0.3 is not activated)."""
        return self._v03

    def activate_v03(self, v03_subsystems: dict) -> None:
        """
        Activate v0.3 subsystem container from a boot_v03() result dict.

        This is idempotent — calling it again replaces the previous container.
        """
        container = _V03Subsystems()
        container.self_model = v03_subsystems.get("self_model")
        container.drift_detector = v03_subsystems.get("drift_detector")
        container.pattern_miner = v03_subsystems.get("pattern_miner")
        container.incident_learner = v03_subsystems.get("incident_learner")
        container.optimization_proposer = v03_subsystems.get("optimization_proposer")
        container.efficiency_reporter = v03_subsystems.get("efficiency_reporter")
        container.task_graph_optimizer = v03_subsystems.get("task_graph_optimizer")
        container.cost_accountant = v03_subsystems.get("cost_accountant")
        container.token_economy = v03_subsystems.get("token_economy")
        container.attention_runtime = v03_subsystems.get("attention_runtime")
        container.cognition_tracer = v03_subsystems.get("cognition_tracer")
        container.memory_flow_tracer = v03_subsystems.get("memory_flow_tracer")
        self._v03 = container

    def health(self) -> dict:
        """Quick health check across all subsystems."""
        result = {
            "version": __version__,
            "memory": self.memory.stats(),
            "somatic": self.somatic.bus.current_state(),
            "attention": self.somatic.attention.current_state().to_dict(),
            "governance_stats": self.governance.audit_log.stats(hours=1),
            "agents_registered": len(self.agents.registry.all_agents()),
            "observability": {
                "active_traces": len(self.observability.tracer._traces)
                if hasattr(self.observability.tracer, '_traces') else 0,
            },
        }

        if self._v03 is not None:
            v03_health: dict = {"active": True}
            if self._v03.self_model is not None:
                try:
                    v03_health["self_model"] = self._v03.self_model.health_summary().to_dict()
                except Exception:
                    v03_health["self_model"] = {"error": "unavailable"}
            if self._v03.cognition_tracer is not None:
                try:
                    v03_health["cognition_tracer"] = self._v03.cognition_tracer.stats()
                except Exception:
                    v03_health["cognition_tracer"] = {"error": "unavailable"}
            if self._v03.memory_flow_tracer is not None:
                try:
                    v03_health["memory_flow"] = self._v03.memory_flow_tracer.get_flow_summary().to_dict()
                except Exception:
                    v03_health["memory_flow"] = {"error": "unavailable"}
            if self._v03.token_economy is not None:
                try:
                    v03_health["token_economy"] = self._v03.token_economy.get_utilization()
                except Exception:
                    v03_health["token_economy"] = {"error": "unavailable"}
            if self._v03.cost_accountant is not None:
                try:
                    v03_health["context_costs"] = self._v03.cost_accountant.get_system_costs().to_dict()
                except Exception:
                    v03_health["context_costs"] = {"error": "unavailable"}
            result["v03"] = v03_health

        return result

    def shutdown(self) -> None:
        """Graceful shutdown — save all agent states and memory access counts."""
        if self._v03 is not None:
            if self._integration_bus is not None:
                try:
                    self._integration_bus.unwire_v03()
                except Exception:
                    pass
            self._v03 = None

        self.memory.save_access_counts()
        for agent in self.agents.registry.all_agents():
            agent.save_state()


class _SomaticSubsystem:
    __slots__ = (
        "bus", "attention", "monitor", "anomaly_stream",
        "normalizer", "correlator", "rate_tracker", "analytics",
    )

    def __init__(self, bus, attention, monitor, anomaly_stream):
        self.bus = bus
        self.attention = attention
        self.monitor = monitor
        self.anomaly_stream = anomaly_stream
        self.normalizer = None
        self.correlator = None
        self.rate_tracker = None
        self.analytics = None


class _GovernanceSubsystem:
    __slots__ = (
        "policy_engine", "validator", "anomaly_detector", "audit_log",
        "tool_permissions", "mandatory_gate", "unified_router",
    )

    def __init__(self, policy_engine, validator, anomaly_detector, audit_log):
        self.policy_engine = policy_engine
        self.validator = validator
        self.anomaly_detector = anomaly_detector
        self.audit_log = audit_log
        self.tool_permissions = None
        self.mandatory_gate = None
        self.unified_router = None


class _ContextSubsystem:
    __slots__ = (
        "budget_manager", "retriever", "kernel_retriever",
        "compressor", "assembler", "injection_logger",
    )

    def __init__(
        self, budget_manager, retriever, kernel_retriever,
        compressor, assembler, injection_logger,
    ):
        self.budget_manager = budget_manager
        self.retriever = retriever
        self.kernel_retriever = kernel_retriever
        self.compressor = compressor
        self.assembler = assembler
        self.injection_logger = injection_logger


class _TaskGraphSubsystem:
    __slots__ = ("scheduler", "checkpoint", "executor", "failure_propagator", "visualizer")

    def __init__(self, scheduler, checkpoint, executor):
        self.scheduler = scheduler
        self.checkpoint = checkpoint
        self.executor = executor
        self.failure_propagator = None
        self.visualizer = None


class _AgentSubsystem:
    __slots__ = ("registry", "orchestrator", "isolation_manager")

    def __init__(self, registry, orchestrator, isolation_manager=None):
        self.registry = registry
        self.orchestrator = orchestrator
        self.isolation_manager = isolation_manager


class _ObservabilitySubsystem:
    __slots__ = ("tracer", "metrics", "telemetry", "dashboard", "decision_log", "trace_schema", "system_report")

    def __init__(self, tracer, metrics, telemetry, dashboard):
        self.tracer = tracer
        self.metrics = metrics
        self.telemetry = telemetry
        self.dashboard = dashboard
        self.decision_log = None
        self.trace_schema = None
        self.system_report = None


class _V03Subsystems:
    """Container for v0.3 opt-in subsystems."""

    __slots__ = (
        "self_model",
        "drift_detector",
        "pattern_miner",
        "incident_learner",
        "optimization_proposer",
        "efficiency_reporter",
        "task_graph_optimizer",
        "cost_accountant",
        "token_economy",
        "attention_runtime",
        "cognition_tracer",
        "memory_flow_tracer",
    )

    def __init__(self):
        self.self_model = None
        self.drift_detector = None
        self.pattern_miner = None
        self.incident_learner = None
        self.optimization_proposer = None
        self.efficiency_reporter = None
        self.task_graph_optimizer = None
        self.cost_accountant = None
        self.token_economy = None
        self.attention_runtime = None
        self.cognition_tracer = None
        self.memory_flow_tracer = None
