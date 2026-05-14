"""
Bus Consistency Checker — Verifies IntegrationBus connections are healthy.

Checks all 29 expected connections (16 v0.2 + 13 v0.3), detects stacked
monkey-patches, reports listener counts, and provides AST-based static
fallback when no bus instance is available.
"""

from __future__ import annotations

import ast
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("architecture.graph_truth_layer.bus_consistency_checker")

EXPECTED_V02_CONNECTIONS = [
    "somatic_to_scheduler",
    "somatic_to_context",
    "attention_to_governance",
    "governance_to_audit",
    "tasks_to_tracer",
    "attention_to_agents",
    "memory_metrics",
    "injection_to_tracer",
    "failure_propagation",
    "checkpoint_cleanup",
    "mandatory_gate_audit",
    "tool_permission_somatic",
    "signal_correlator",
    "rate_tracker",
    "analytics_to_health",
    "agent_decision_log",
]

EXPECTED_V03_CONNECTIONS = [
    "self_model_drift",
    "drift_to_somatic",
    "execution_to_patterns",
    "incidents_to_learner",
    "optimizer_to_scheduler",
    "context_costs",
    "budget_to_economy",
    "attention_runtime",
    "throttle_to_scheduler",
    "cognition_tracing",
    "memory_flow",
    "evolution_audit",
    "evolution_to_governance",
]

KNOWN_MONKEY_PATCHED_METHODS = [
    "governance.validator.validate",
    "memory.recall",
    "governance.mandatory_gate.check",
    "observability.telemetry.complete_task",
    "kernel.health",
    "context.budget_manager.allocate",
    "memory.store",
    "identity.self_model.snapshot",
    "observability.drift_detector.detect",
    "memory.evolution.reporter.generate_report",
    "memory.evolution.proposer.propose_from_patterns",
]


@dataclass
class ConnectionStatus:
    """Status of a single expected bus connection."""
    name: str
    expected: bool
    found: bool
    mechanism: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "expected": self.expected,
            "found": self.found,
            "mechanism": self.mechanism,
        }


@dataclass
class MonkeyPatchStatus:
    """Status of a monkey-patched method."""
    method_path: str
    original_owner: str
    stack_depth: int
    is_safe: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "method_path": self.method_path,
            "original_owner": self.original_owner,
            "stack_depth": self.stack_depth,
            "is_safe": self.is_safe,
        }


@dataclass
class ListenerStatus:
    """Status of a subscriber/listener API."""
    api_name: str
    listener_count: int
    has_unsubscribe: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_name": self.api_name,
            "listener_count": self.listener_count,
            "has_unsubscribe": self.has_unsubscribe,
        }


@dataclass
class BusConsistencyReport:
    """Full consistency check result for the IntegrationBus."""
    connections: list[ConnectionStatus] = field(default_factory=list)
    monkey_patches: list[MonkeyPatchStatus] = field(default_factory=list)
    listeners: list[ListenerStatus] = field(default_factory=list)
    total_expected: int = 0
    total_found: int = 0
    is_consistent: bool = True
    checked_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        missing = [c.to_dict() for c in self.connections if not c.found]
        return {
            "total_expected": self.total_expected,
            "total_found": self.total_found,
            "is_consistent": self.is_consistent,
            "missing_connections": missing,
            "monkey_patch_count": len(self.monkey_patches),
            "monkey_patches": [m.to_dict() for m in self.monkey_patches],
            "listener_apis": [l.to_dict() for l in self.listeners],
            "checked_at": self.checked_at,
        }


class BusConsistencyChecker:
    """
    Verifies IntegrationBus connections are healthy and consistent.

    Supports two modes:
      1. Runtime mode: inspects a live bus instance
      2. Static mode: AST-based fallback when no bus instance is available
    """

    def __init__(self, root_dir: Path):
        self._root = root_dir.resolve()

    def check(self, bus: Any = None) -> BusConsistencyReport:
        """Run all consistency checks against the integration bus."""
        logger.info("Checking bus consistency...")
        start = time.monotonic()

        if bus is not None:
            connections = self._check_expected_connections(bus)
            monkey_patches = self._check_monkey_patches(bus)
            listeners = self._check_listener_counts(bus)
        else:
            connections = self._static_check()
            monkey_patches = []
            listeners = []

        total_expected = len(EXPECTED_V02_CONNECTIONS) + len(EXPECTED_V03_CONNECTIONS)
        total_found = sum(1 for c in connections if c.found)
        is_consistent = all(c.found for c in connections if c.expected)

        elapsed = (time.monotonic() - start) * 1000
        report = BusConsistencyReport(
            connections=connections,
            monkey_patches=monkey_patches,
            listeners=listeners,
            total_expected=total_expected,
            total_found=total_found,
            is_consistent=is_consistent,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            "Bus consistency: %d/%d connections found, consistent=%s (%.1fms)",
            total_found, total_expected, is_consistent, elapsed,
        )
        return report

    def _check_expected_connections(self, bus: Any) -> list[ConnectionStatus]:
        """Verify all 29 expected connections exist on the bus instance."""
        results: list[ConnectionStatus] = []

        for conn_name in EXPECTED_V02_CONNECTIONS:
            method_name = f"_wire_{conn_name}"
            has_method = hasattr(bus, method_name) and callable(getattr(bus, method_name))
            is_wired = getattr(bus, '_wired', False)

            results.append(ConnectionStatus(
                name=conn_name,
                expected=True,
                found=has_method and is_wired,
                mechanism="callback" if conn_name in (
                    "somatic_to_scheduler", "somatic_to_context",
                    "attention_to_governance", "tasks_to_tracer",
                    "attention_to_agents", "injection_to_tracer",
                    "failure_propagation", "checkpoint_cleanup",
                    "signal_correlator", "rate_tracker",
                ) else "monkey_patch",
            ))

        v03_connections = getattr(bus, '_v03_connections', [])
        for conn_name in EXPECTED_V03_CONNECTIONS:
            results.append(ConnectionStatus(
                name=conn_name,
                expected=True,
                found=conn_name in v03_connections,
                mechanism="v03_wire",
            ))

        return results

    def _check_monkey_patches(self, bus: Any) -> list[MonkeyPatchStatus]:
        """Detect stacked monkey-patches by inspecting function wrappers."""
        results: list[MonkeyPatchStatus] = []
        kernel = getattr(bus, 'kernel', None)
        if kernel is None:
            return results

        patch_targets = [
            ("governance.validator.validate", kernel, ["governance", "validator", "validate"]),
            ("memory.recall", kernel, ["memory", "recall"]),
            ("governance.mandatory_gate.check", kernel, ["governance", "mandatory_gate", "check"]),
            ("observability.telemetry.complete_task", kernel, ["observability", "telemetry", "complete_task"]),
            ("kernel.health", kernel, ["health"]),
        ]

        for method_path, obj, attrs in patch_targets:
            target = obj
            for attr in attrs:
                target = getattr(target, attr, None)
                if target is None:
                    break

            if target is None:
                continue

            stack_depth = 0
            current = target
            while hasattr(current, '__wrapped__'):
                stack_depth += 1
                current = current.__wrapped__

            # Detect closure-based wrapping by checking qualname
            if hasattr(target, '__qualname__'):
                if '<locals>' in target.__qualname__:
                    stack_depth = max(stack_depth, 1)

            original_owner = getattr(target, '__module__', 'unknown')

            results.append(MonkeyPatchStatus(
                method_path=method_path,
                original_owner=original_owner,
                stack_depth=stack_depth,
                is_safe=stack_depth <= 3,
            ))

        return results

    def _check_listener_counts(self, bus: Any) -> list[ListenerStatus]:
        """Report listener counts for subscriber APIs on the bus's kernel."""
        results: list[ListenerStatus] = []
        kernel = getattr(bus, 'kernel', None)
        if kernel is None:
            return results

        subscriber_apis = [
            ("somatic.attention.on_change", kernel, ["somatic", "attention"]),
            ("task_graph.scheduler.on_event", kernel, ["task_graph", "scheduler"]),
            ("somatic.bus.on_signal", kernel, ["somatic", "bus"]),
        ]

        for api_name, obj, attrs in subscriber_apis:
            target = obj
            for attr in attrs:
                target = getattr(target, attr, None)
                if target is None:
                    break

            if target is None:
                continue

            listener_count = 0
            for attr_name in ('_listeners', '_callbacks', '_handlers', '_subscribers'):
                listeners = getattr(target, attr_name, None)
                if listeners is not None:
                    listener_count = len(listeners) if hasattr(listeners, '__len__') else 0
                    break

            has_unsubscribe = hasattr(target, 'off') or hasattr(target, 'unsubscribe')

            results.append(ListenerStatus(
                api_name=api_name,
                listener_count=listener_count,
                has_unsubscribe=has_unsubscribe,
            ))

        return results

    def _static_check(self) -> list[ConnectionStatus]:
        """AST-based fallback when no bus instance is available."""
        bus_file = self._root / "kernel" / "integration_bus.py"
        results: list[ConnectionStatus] = []

        if not bus_file.exists():
            logger.warning("integration_bus.py not found at %s", bus_file)
            for conn_name in EXPECTED_V02_CONNECTIONS + EXPECTED_V03_CONNECTIONS:
                results.append(ConnectionStatus(
                    name=conn_name, expected=True, found=False,
                    mechanism="unknown",
                ))
            return results

        try:
            source = bus_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(bus_file))
        except (SyntaxError, OSError) as exc:
            logger.warning("Failed to parse integration_bus.py: %s", exc)
            for conn_name in EXPECTED_V02_CONNECTIONS + EXPECTED_V03_CONNECTIONS:
                results.append(ConnectionStatus(
                    name=conn_name, expected=True, found=False,
                    mechanism="parse_error",
                ))
            return results

        found_methods: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_wire_"):
                    found_methods.add(node.name.removeprefix("_wire_"))

        for conn_name in EXPECTED_V02_CONNECTIONS:
            results.append(ConnectionStatus(
                name=conn_name,
                expected=True,
                found=conn_name in found_methods,
                mechanism="static_analysis",
            ))

        # v0.3 connections are registered in _v03_connections list at runtime;
        # for static analysis, check if the wire method exists in wire_v03 body
        v03_method_bodies = self._extract_v03_connection_names(tree)
        for conn_name in EXPECTED_V03_CONNECTIONS:
            results.append(ConnectionStatus(
                name=conn_name,
                expected=True,
                found=conn_name in v03_method_bodies,
                mechanism="static_analysis",
            ))

        return results

    def _extract_v03_connection_names(self, tree: ast.Module) -> set[str]:
        """Extract v0.3 connection names from append calls in wire_v03 and sub-methods."""
        names: set[str] = set()

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            func = node.func
            if not isinstance(func, ast.Attribute):
                continue

            if func.attr != "append":
                continue

            if not isinstance(func.value, ast.Attribute):
                continue

            if func.value.attr != "_v03_connections":
                continue

            if node.args and isinstance(node.args[0], ast.Constant):
                names.add(node.args[0].value)

        return names
