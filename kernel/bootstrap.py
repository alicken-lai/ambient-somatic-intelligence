"""
Kernel Bootstrap — System initialization and subsystem wiring.

Provides the standard boot sequence for Ambient OS:

  1. Initialize somatic signal bus (the "nervous system")
  2. Initialize governance (safety first — must be ready before anything executes)
  3. Initialize context engine (memory retrieval and budget management)
  4. Initialize task graph runtime (DAG scheduler)
  5. Initialize agent runtime (register all specialist agents)
  6. Initialize observability (tracing, metrics, telemetry)
  7. Wire integration bus (connect all subsystems)
  8. Run startup health check

Usage:
    from kernel.bootstrap import boot, boot_minimal

    # Full boot — all subsystems + integration wiring
    kernel = boot()

    # Minimal boot — subsystems only, no wiring (for testing)
    kernel = boot_minimal()
"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("kernel.bootstrap")


def boot(
    register_default_agents: bool = True,
    enable_env_monitor: bool = False,
    log_level: int = logging.INFO,
) -> "AmbientKernel":
    """
    Full kernel boot sequence.

    Args:
        register_default_agents: Whether to create and register the 6 default specialist agents.
        enable_env_monitor: Whether to start the environment monitor (resource sensing).
                            Disabled by default as it spawns a background thread.
        log_level: Logging level for kernel components.

    Returns:
        A fully initialized and wired AmbientKernel instance.
    """
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    start = time.monotonic()
    logger.info("Ambient OS kernel boot sequence starting...")

    from kernel import AmbientKernel

    kernel = AmbientKernel.boot()

    if register_default_agents:
        _register_default_agents(kernel)

    if enable_env_monitor and hasattr(kernel.somatic.monitor, 'start'):
        kernel.somatic.monitor.start()
        logger.info("  Environment monitor started")

    duration_ms = (time.monotonic() - start) * 1000
    agent_count = len(kernel.agents.registry.all_agents())

    logger.info(
        f"Ambient OS kernel boot complete in {duration_ms:.0f}ms — "
        f"{agent_count} agents registered, integration bus wired"
    )

    return kernel


def boot_minimal() -> "AmbientKernel":
    """
    Minimal boot — subsystems initialized but NOT wired.

    Use for unit testing individual subsystems in isolation.
    """
    from kernel import AmbientKernel
    return AmbientKernel()


def _register_default_agents(kernel: "AmbientKernel") -> None:
    """Register the default set of specialist agents with isolation profiles."""
    try:
        from agents.specialists import (
            FrontendAgent,
            BackendAgent,
            TestingAgent,
            GuardianAgent,
            MemoryManagerAgent,
            PlannerAgent,
        )
    except ImportError as e:
        logger.warning(f"Could not import specialist agents: {e}")
        return

    agents = [
        FrontendAgent(),
        BackendAgent(),
        TestingAgent(),
        GuardianAgent(),
        MemoryManagerAgent(),
        PlannerAgent(),
    ]

    isolation_mgr = kernel.agents.isolation_manager

    for agent in agents:
        agent.load_state()
        kernel.agents.registry.register(agent)

        if isolation_mgr and hasattr(agent, 'default_retrieval_profile'):
            profile = agent.default_retrieval_profile()
            mem_slice = isolation_mgr.register(profile)
            agent.retrieval_profile = profile
            agent.memory_slice = mem_slice
            logger.debug(f"  Isolation profile set for: {agent.name} ({agent.agent_id})")

        logger.debug(f"  Registered agent: {agent.name} ({agent.agent_id})")


def boot_v03(
    kernel: "AmbientKernel",
    enable_persistence: bool = True,
) -> dict[str, Any]:
    """
    Boot v0.3 subsystems on top of an already-booted v0.2 kernel.

    Instantiates v0.3 subsystems using existing kernel components,
    wires them via IntegrationBus.wire_v03(), and runs health checks.

    Args:
        kernel: A fully booted v0.2 AmbientKernel instance.
        enable_persistence: Whether v0.3 subsystem tracers persist to disk.

    Returns:
        A dict of v0.3 subsystem instances, keyed by subsystem name.
    """
    start = time.monotonic()
    logger.info("v0.3 subsystem boot sequence starting...")

    v03: dict[str, Any] = {}

    # ── 1. Cognitive Self-Model ──────────────────────────────────────
    try:
        from identity.cognitive_self_model.self_model import CognitiveSelfModel
        self_model = CognitiveSelfModel(kernel=kernel)
        self_model.build()
        v03["self_model"] = self_model
        logger.info("  [v0.3] CognitiveSelfModel built")
    except Exception as exc:
        logger.warning("  [v0.3] CognitiveSelfModel failed: %s", exc)

    # ── 2. Drift Detector ────────────────────────────────────────────
    try:
        from observability.drift_detection.drift_detector import DriftDetector
        drift_detector = DriftDetector()
        v03["drift_detector"] = drift_detector
        logger.info("  [v0.3] DriftDetector initialized")
    except Exception as exc:
        logger.warning("  [v0.3] DriftDetector failed: %s", exc)

    # ── 3. Memory Evolution (Pattern Miner + Incident Learner + Proposer + Reporter) ──
    try:
        from memory.evolution.pattern_miner import PatternMiner
        from memory.evolution.incident_learner import IncidentLearner
        from memory.evolution.optimization_proposer import OptimizationProposer
        from memory.evolution.efficiency_reporter import EfficiencyReporter

        v03["pattern_miner"] = PatternMiner()
        v03["incident_learner"] = IncidentLearner()
        v03["optimization_proposer"] = OptimizationProposer()
        v03["efficiency_reporter"] = EfficiencyReporter()
        logger.info("  [v0.3] Memory Evolution subsystem initialized")
    except Exception as exc:
        logger.warning("  [v0.3] Memory Evolution failed: %s", exc)

    # ── 4. Task Graph Optimizer ──────────────────────────────────────
    try:
        from runtime.task_graph_optimizer.optimizer import TaskGraphOptimizer
        v03["task_graph_optimizer"] = TaskGraphOptimizer()
        logger.info("  [v0.3] TaskGraphOptimizer initialized")
    except Exception as exc:
        logger.warning("  [v0.3] TaskGraphOptimizer failed: %s", exc)

    # ── 5. Context Economy ───────────────────────────────────────────
    try:
        from context.context_economy.cost_accountant import ContextCostAccountant
        from context.context_economy.token_economy import TokenEconomy

        v03["cost_accountant"] = ContextCostAccountant(persist=enable_persistence)
        v03["token_economy"] = TokenEconomy()
        logger.info("  [v0.3] Context Economy initialized")
    except Exception as exc:
        logger.warning("  [v0.3] Context Economy failed: %s", exc)

    # ── 6. Somatic Attention Runtime ─────────────────────────────────
    try:
        from somatic.attention_runtime.attention_runtime import SomaticAttentionRuntime
        attention_runtime = SomaticAttentionRuntime(
            bus=kernel.somatic.bus,
            attention_manager=kernel.somatic.attention,
        )
        v03["attention_runtime"] = attention_runtime
        logger.info("  [v0.3] SomaticAttentionRuntime initialized")
    except Exception as exc:
        logger.warning("  [v0.3] SomaticAttentionRuntime failed: %s", exc)

    # ── 7. Recursive Observability ───────────────────────────────────
    try:
        from observability.recursive_runtime.cognition_tracer import CognitionTracer
        from observability.recursive_runtime.memory_flow_tracer import MemoryFlowTracer

        v03["cognition_tracer"] = CognitionTracer(persist=enable_persistence)
        v03["memory_flow_tracer"] = MemoryFlowTracer(persist=enable_persistence)
        logger.info("  [v0.3] Recursive Observability initialized")
    except Exception as exc:
        logger.warning("  [v0.3] Recursive Observability failed: %s", exc)

    # ── 8. Wire v0.3 Integration Bus ─────────────────────────────────
    if kernel.integration_bus is not None:
        try:
            kernel.integration_bus.wire_v03(
                self_model=v03.get("self_model"),
                drift_detector=v03.get("drift_detector"),
                pattern_miner=v03.get("pattern_miner"),
                incident_learner=v03.get("incident_learner"),
                task_graph_optimizer=v03.get("task_graph_optimizer"),
                cost_accountant=v03.get("cost_accountant"),
                token_economy=v03.get("token_economy"),
                attention_runtime=v03.get("attention_runtime"),
                cognition_tracer=v03.get("cognition_tracer"),
                memory_flow_tracer=v03.get("memory_flow_tracer"),
                evolution_reporter=v03.get("efficiency_reporter"),
                optimization_proposer=v03.get("optimization_proposer"),
            )
            logger.info("  [v0.3] IntegrationBus v0.3 wired")
        except Exception as exc:
            logger.warning("  [v0.3] IntegrationBus v0.3 wiring failed: %s", exc)

    # ── 9. Activate on kernel ────────────────────────────────────────
    if hasattr(kernel, 'activate_v03'):
        kernel.activate_v03(v03)

    duration_ms = (time.monotonic() - start) * 1000
    logger.info(
        "v0.3 subsystem boot complete in %.0fms — %d subsystems initialized",
        duration_ms, len(v03),
    )
    return v03


def verify_v03(
    kernel: "AmbientKernel",
    v03_subsystems: dict[str, Any],
) -> dict[str, Any]:
    """
    Post-boot verification for v0.3 subsystems.

    Verifies all v0.3 subsystems are properly initialized and
    IntegrationBus v0.3 connections are active.

    Returns:
        A dict with per-subsystem health status.
    """
    results: dict[str, Any] = {"timestamp": time.time(), "checks": {}}

    checks = {
        "self_model": lambda: (
            v03_subsystems.get("self_model") is not None
            and callable(getattr(v03_subsystems["self_model"], "health_summary", None))
        ),
        "drift_detector": lambda: (
            v03_subsystems.get("drift_detector") is not None
            and callable(getattr(v03_subsystems["drift_detector"], "detect", None))
        ),
        "pattern_miner": lambda: (
            v03_subsystems.get("pattern_miner") is not None
            and callable(getattr(v03_subsystems["pattern_miner"], "mine_success_patterns", None))
        ),
        "incident_learner": lambda: (
            v03_subsystems.get("incident_learner") is not None
            and callable(getattr(v03_subsystems["incident_learner"], "analyze_incidents", None))
        ),
        "optimization_proposer": lambda: (
            v03_subsystems.get("optimization_proposer") is not None
            and callable(getattr(v03_subsystems["optimization_proposer"], "propose_from_patterns", None))
        ),
        "efficiency_reporter": lambda: (
            v03_subsystems.get("efficiency_reporter") is not None
            and callable(getattr(v03_subsystems["efficiency_reporter"], "generate_report", None))
        ),
        "task_graph_optimizer": lambda: (
            v03_subsystems.get("task_graph_optimizer") is not None
            and callable(getattr(v03_subsystems["task_graph_optimizer"], "optimize", None))
        ),
        "cost_accountant": lambda: (
            v03_subsystems.get("cost_accountant") is not None
            and callable(getattr(v03_subsystems["cost_accountant"], "record_cost", None))
        ),
        "token_economy": lambda: (
            v03_subsystems.get("token_economy") is not None
            and callable(getattr(v03_subsystems["token_economy"], "allocate_budget", None))
        ),
        "attention_runtime": lambda: (
            v03_subsystems.get("attention_runtime") is not None
            and callable(getattr(v03_subsystems["attention_runtime"], "process_signal", None))
        ),
        "cognition_tracer": lambda: (
            v03_subsystems.get("cognition_tracer") is not None
            and callable(getattr(v03_subsystems["cognition_tracer"], "trace_decision", None))
        ),
        "memory_flow_tracer": lambda: (
            v03_subsystems.get("memory_flow_tracer") is not None
            and callable(getattr(v03_subsystems["memory_flow_tracer"], "trace_recall", None))
        ),
        "v03_bus_wired": lambda: (
            kernel.integration_bus is not None
            and len(getattr(kernel.integration_bus, '_v03_connections', [])) > 0
        ),
        "kernel_v03_active": lambda: (
            hasattr(kernel, 'v03') and kernel.v03 is not None
        ),
    }

    all_ok = True
    for name, check_fn in checks.items():
        try:
            passed = check_fn()
            results["checks"][name] = {"status": "ok" if passed else "fail"}
            if not passed:
                all_ok = False
        except Exception as e:
            results["checks"][name] = {"status": "error", "error": str(e)}
            all_ok = False

    results["all_ok"] = all_ok
    results["total_checks"] = len(checks)
    results["passed"] = sum(1 for c in results["checks"].values() if c["status"] == "ok")

    return results


def verify_boot(kernel: "AmbientKernel") -> dict[str, Any]:
    """
    Post-boot verification — checks that all subsystems are responsive.

    Returns a dict with per-subsystem health status.
    """
    results: dict[str, Any] = {"timestamp": time.time(), "checks": {}}

    checks = {
        "memory_kernel": lambda: kernel.memory is not None and callable(getattr(kernel.memory, 'recall', None)),
        "somatic_bus": lambda: kernel.somatic.bus.current_state() is not None,
        "attention_manager": lambda: kernel.somatic.attention.current_state() is not None,
        "policy_engine": lambda: kernel.governance.policy_engine is not None,
        "execution_validator": lambda: kernel.governance.validator is not None,
        "audit_log": lambda: kernel.governance.audit_log is not None,
        "tool_permissions": lambda: kernel.governance.tool_permissions is not None and callable(getattr(kernel.governance.tool_permissions, 'check', None)),
        "mandatory_gate": lambda: kernel.governance.mandatory_gate is not None and callable(getattr(kernel.governance.mandatory_gate, 'check', None)),
        "unified_router": lambda: kernel.governance.unified_router is not None and callable(getattr(kernel.governance.unified_router, 'check', None)),
        "context_assembler": lambda: kernel.context.assembler is not None,
        "budget_manager": lambda: kernel.context.budget_manager is not None,
        "injection_logger": lambda: kernel.context.injection_logger is not None and callable(getattr(kernel.context.injection_logger, 'log_injection', None)),
        "kernel_retriever": lambda: kernel.context.kernel_retriever is not None and callable(getattr(kernel.context.kernel_retriever, 'retrieve', None)),
        "scheduler": lambda: kernel.task_graph.scheduler is not None,
        "scheduler_sync": lambda: callable(getattr(kernel.task_graph.scheduler, 'execute_sync', None)),
        "checkpoint_manager": lambda: kernel.task_graph.checkpoint is not None,
        "failure_propagator": lambda: kernel.task_graph.failure_propagator is not None and callable(getattr(kernel.task_graph.failure_propagator, 'propagate', None)),
        "dag_visualizer": lambda: kernel.task_graph.visualizer is not None and callable(getattr(kernel.task_graph.visualizer, 'to_ascii', None)),
        "agent_registry": lambda: kernel.agents.registry is not None,
        "agent_isolation_manager": lambda: kernel.agents.isolation_manager is not None and callable(getattr(kernel.agents.isolation_manager, 'get_slice', None)),
        "orchestrator": lambda: kernel.agents.orchestrator is not None,
        "tracer": lambda: kernel.observability.tracer is not None,
        "metrics_collector": lambda: kernel.observability.metrics is not None,
        "integration_bus": lambda: kernel.integration_bus is not None and kernel.integration_bus.is_wired,
        "signal_normalizer": lambda: kernel.somatic.normalizer is not None and callable(getattr(kernel.somatic.normalizer, 'normalize', None)),
        "signal_correlator": lambda: kernel.somatic.correlator is not None and callable(getattr(kernel.somatic.correlator, 'correlate', None)),
        "rate_tracker": lambda: kernel.somatic.rate_tracker is not None and callable(getattr(kernel.somatic.rate_tracker, 'current_rate', None)),
        "signal_analytics": lambda: kernel.somatic.analytics is not None and callable(getattr(kernel.somatic.analytics, 'health_score', None)),
        "agent_decision_log": lambda: kernel.observability.decision_log is not None and callable(getattr(kernel.observability.decision_log, 'log_decision', None)),
        "system_report": lambda: kernel.observability.system_report is not None and callable(getattr(kernel.observability.system_report, 'generate', None)),
        "trace_schema": lambda: kernel.observability.trace_schema is not None and callable(getattr(kernel.observability.trace_schema, 'validate_event', None)),
    }

    all_ok = True
    for name, check_fn in checks.items():
        try:
            passed = check_fn()
            results["checks"][name] = {"status": "ok" if passed else "fail"}
            if not passed:
                all_ok = False
        except Exception as e:
            results["checks"][name] = {"status": "error", "error": str(e)}
            all_ok = False

    results["all_ok"] = all_ok
    results["total_checks"] = len(checks)
    results["passed"] = sum(1 for c in results["checks"].values() if c["status"] == "ok")

    return results
