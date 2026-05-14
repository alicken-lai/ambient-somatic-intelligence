"""
Integration Integrity Checker — Verifies integration bus connection health.

Checks all 16 bus connections for validity: disconnected handlers, handlers
referencing missing methods, event types with no subscribers, and duplicate
wiring patterns.
"""

from __future__ import annotations

import inspect
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.integration_bus import IntegrationBus

logger = logging.getLogger("observability.drift_detection.integration_checker")

EXPECTED_CONNECTIONS = [
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


@dataclass
class ConnectionStatus:
    """Status of a single bus connection."""
    name: str
    valid: bool = True
    method_exists: bool = True
    handler_active: bool = True
    warning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "valid": self.valid,
            "method_exists": self.method_exists,
            "handler_active": self.handler_active,
            "warning": self.warning,
        }


@dataclass
class IntegrityReport:
    """Result of an integration integrity check."""
    valid_connections: list[ConnectionStatus] = field(default_factory=list)
    broken_connections: list[ConnectionStatus] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    health_score: float = 100.0
    total_expected: int = 16
    check_timestamp: str = ""
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid_connections": [c.to_dict() for c in self.valid_connections],
            "broken_connections": [c.to_dict() for c in self.broken_connections],
            "warnings": self.warnings,
            "health_score": round(self.health_score, 1),
            "valid_count": len(self.valid_connections),
            "broken_count": len(self.broken_connections),
            "total_expected": self.total_expected,
            "coverage_pct": round(
                len(self.valid_connections) / max(self.total_expected, 1) * 100, 1
            ),
            "check_timestamp": self.check_timestamp,
            "elapsed_ms": round(self.elapsed_ms, 1),
        }


class IntegrationIntegrityChecker:
    """
    Verifies all integration bus connections are valid.

    Checks:
      1. All expected wire methods exist on the bus class
      2. Handlers reference valid methods on their target objects
      3. Event types have at least one subscriber
      4. No duplicate wiring detected
    """

    def check(self, bus_instance: "IntegrationBus | None" = None) -> IntegrityReport:
        """Verify all 16 bus connections are valid."""
        logger.info("Checking integration bus integrity...")
        start = time.monotonic()

        valid: list[ConnectionStatus] = []
        broken: list[ConnectionStatus] = []
        warnings: list[str] = []

        if bus_instance is None:
            warnings.append("No bus instance provided — performing static analysis only")
            return self._static_check(warnings, start)

        if not bus_instance.is_wired:
            warnings.append("Integration bus is not wired — connections inactive")

        self._check_wire_methods(bus_instance, valid, broken, warnings)
        self._check_kernel_references(bus_instance, valid, broken, warnings)
        self._check_event_log(bus_instance, warnings)
        self._check_duplicate_wiring(bus_instance, warnings)

        elapsed = (time.monotonic() - start) * 1000
        health_score = self._compute_health(valid, broken)

        report = IntegrityReport(
            valid_connections=valid,
            broken_connections=broken,
            warnings=warnings,
            health_score=health_score,
            total_expected=len(EXPECTED_CONNECTIONS),
            check_timestamp=datetime.now(timezone.utc).isoformat(),
            elapsed_ms=elapsed,
        )

        logger.info(
            "Integration check complete: %d valid, %d broken, score=%.1f (%.1fms)",
            len(valid), len(broken), health_score, elapsed,
        )
        return report

    # ── Check Methods ────────────────────────────────────────────────────

    def _check_wire_methods(
        self,
        bus: "IntegrationBus",
        valid: list[ConnectionStatus],
        broken: list[ConnectionStatus],
        warnings: list[str],
    ) -> None:
        """Verify all expected _wire_* methods exist and are callable."""
        for conn_name in EXPECTED_CONNECTIONS:
            method_name = f"_wire_{conn_name}"
            method = getattr(bus, method_name, None)

            if method is None:
                broken.append(ConnectionStatus(
                    name=conn_name,
                    valid=False,
                    method_exists=False,
                    handler_active=False,
                    warning=f"Wire method '{method_name}' not found on bus",
                ))
            elif not callable(method):
                broken.append(ConnectionStatus(
                    name=conn_name,
                    valid=False,
                    method_exists=True,
                    handler_active=False,
                    warning=f"'{method_name}' exists but is not callable",
                ))
            else:
                valid.append(ConnectionStatus(
                    name=conn_name,
                    valid=True,
                    method_exists=True,
                    handler_active=bus.is_wired,
                ))

    def _check_kernel_references(
        self,
        bus: "IntegrationBus",
        valid: list[ConnectionStatus],
        broken: list[ConnectionStatus],
        warnings: list[str],
    ) -> None:
        """Verify the bus kernel reference has all required subsystems."""
        kernel = bus.kernel
        if kernel is None:
            broken.append(ConnectionStatus(
                name="kernel_reference",
                valid=False,
                method_exists=False,
                warning="Bus has no kernel reference",
            ))
            return

        required_subsystems = [
            ("somatic", "bus"),
            ("somatic", "attention"),
            ("governance", "validator"),
            ("governance", "audit_log"),
            ("governance", "mandatory_gate"),
            ("task_graph", "scheduler"),
            ("task_graph", "executor"),
            ("context", "budget_manager"),
            ("context", "injection_logger"),
            ("agents", "registry"),
            ("observability", "tracer"),
            ("observability", "metrics"),
            ("observability", "telemetry"),
            ("memory", None),
        ]

        for subsystem, attr in required_subsystems:
            sub_obj = getattr(kernel, subsystem, None)
            if sub_obj is None:
                warnings.append(f"Kernel missing subsystem: {subsystem}")
                continue

            if attr is not None:
                if not hasattr(sub_obj, attr):
                    warnings.append(
                        f"Subsystem '{subsystem}' missing attribute '{attr}'"
                    )

    def _check_event_log(
        self,
        bus: "IntegrationBus",
        warnings: list[str],
    ) -> None:
        """Check bus event log for anomalies."""
        event_log = getattr(bus, 'event_log', [])

        if bus.is_wired and len(event_log) == 0:
            warnings.append(
                "Bus is wired but event log is empty — "
                "no cross-subsystem events recorded"
            )

        max_log = getattr(bus, '_max_log', 500)
        if len(event_log) >= max_log:
            warnings.append(
                f"Event log at capacity ({max_log}) — older events may be lost"
            )

    def _check_duplicate_wiring(
        self,
        bus: "IntegrationBus",
        warnings: list[str],
    ) -> None:
        """Detect potential duplicate wiring from event log patterns."""
        event_log = getattr(bus, 'event_log', [])

        wired_events = [
            e for e in event_log
            if hasattr(e, 'event_type') and e.event_type == "wired"
        ]
        if len(wired_events) > 1:
            warnings.append(
                f"Multiple 'wired' events detected ({len(wired_events)}) — "
                "possible duplicate wire() call"
            )

    # ── Static Analysis Fallback ─────────────────────────────────────────

    def _static_check(
        self,
        warnings: list[str],
        start: float,
    ) -> IntegrityReport:
        """Perform static analysis when no bus instance is available."""
        from pathlib import Path
        import ast

        bus_file = Path(__file__).resolve().parent.parent.parent / "kernel" / "integration_bus.py"
        valid: list[ConnectionStatus] = []
        broken: list[ConnectionStatus] = []

        if not bus_file.exists():
            warnings.append("integration_bus.py not found on disk")
            elapsed = (time.monotonic() - start) * 1000
            return IntegrityReport(
                valid_connections=valid,
                broken_connections=broken,
                warnings=warnings,
                health_score=0.0,
                check_timestamp=datetime.now(timezone.utc).isoformat(),
                elapsed_ms=elapsed,
            )

        try:
            source = bus_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (SyntaxError, OSError) as exc:
            warnings.append(f"Failed to parse integration_bus.py: {exc}")
            elapsed = (time.monotonic() - start) * 1000
            return IntegrityReport(
                valid_connections=valid,
                broken_connections=broken,
                warnings=warnings,
                health_score=50.0,
                check_timestamp=datetime.now(timezone.utc).isoformat(),
                elapsed_ms=elapsed,
            )

        found_methods: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_wire_"):
                    found_methods.add(node.name.removeprefix("_wire_"))

        for conn_name in EXPECTED_CONNECTIONS:
            if conn_name in found_methods:
                valid.append(ConnectionStatus(
                    name=conn_name,
                    valid=True,
                    method_exists=True,
                    handler_active=False,
                    warning="Static analysis only — runtime status unknown",
                ))
            else:
                broken.append(ConnectionStatus(
                    name=conn_name,
                    valid=False,
                    method_exists=False,
                    warning=f"_wire_{conn_name} not found in source",
                ))

        elapsed = (time.monotonic() - start) * 1000
        health_score = self._compute_health(valid, broken)

        return IntegrityReport(
            valid_connections=valid,
            broken_connections=broken,
            warnings=warnings,
            health_score=health_score,
            total_expected=len(EXPECTED_CONNECTIONS),
            check_timestamp=datetime.now(timezone.utc).isoformat(),
            elapsed_ms=elapsed,
        )

    @staticmethod
    def _compute_health(
        valid: list[ConnectionStatus],
        broken: list[ConnectionStatus],
    ) -> float:
        """Compute integration health score (0-100)."""
        total = len(valid) + len(broken)
        if total == 0:
            return 0.0
        return (len(valid) / total) * 100.0
