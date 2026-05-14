"""
Mutation Simulator — Simulate architecture mutations without applying them.

Provides safe exploration of architectural changes:
  - Compute new dependency graphs after proposed changes
  - Identify potential breakage from mutations
  - Estimate performance impact
  - Run what-if analysis for hypothetical scenarios

All operations are purely analytical — no actual system changes are made.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SystemTopology:
    """Represents the current system module topology."""
    modules: dict[str, dict[str, Any]] = field(default_factory=dict)
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    health_scores: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "modules": self.modules,
            "dependencies": self.dependencies,
            "health_scores": self.health_scores,
            "metadata": self.metadata,
            "module_count": len(self.modules),
            "dependency_count": sum(len(v) for v in self.dependencies.values()),
        }


@dataclass
class SimulationResult:
    """Result of simulating proposed changes on the topology."""
    simulation_id: str = field(default_factory=lambda: f"sim_{uuid.uuid4().hex[:12]}")
    simulated_topology: SystemTopology = field(default_factory=SystemTopology)
    changes_applied: list[dict[str, Any]] = field(default_factory=list)
    new_dependencies: list[dict[str, str]] = field(default_factory=list)
    broken_dependencies: list[dict[str, str]] = field(default_factory=list)
    risk_areas: list[dict[str, Any]] = field(default_factory=list)
    performance_estimate: dict[str, Any] = field(default_factory=dict)
    health_score_delta: float = 0.0
    timestamp: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "simulation_id": self.simulation_id,
            "simulated_topology": self.simulated_topology.to_dict(),
            "changes_applied": self.changes_applied,
            "new_dependencies": self.new_dependencies,
            "broken_dependencies": self.broken_dependencies,
            "risk_areas": self.risk_areas,
            "performance_estimate": self.performance_estimate,
            "health_score_delta": round(self.health_score_delta, 4),
            "timestamp": self.timestamp,
        }


@dataclass
class ComparisonReport:
    """Detailed comparison between current and simulated topology."""
    changed_modules: list[str] = field(default_factory=list)
    added_dependencies: list[dict[str, str]] = field(default_factory=list)
    removed_dependencies: list[dict[str, str]] = field(default_factory=list)
    risk_areas: list[dict[str, Any]] = field(default_factory=list)
    health_impact: dict[str, float] = field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "changed_modules": self.changed_modules,
            "added_dependencies": self.added_dependencies,
            "removed_dependencies": self.removed_dependencies,
            "risk_areas": self.risk_areas,
            "health_impact": self.health_impact,
            "summary": self.summary,
        }


class MutationSimulator:
    """
    Simulates architecture mutations without applying them.

    Allows safe exploration of proposed changes by computing their
    effects on the system topology, dependency graph, and health scores.

    Usage:
        simulator = MutationSimulator()

        current = SystemTopology(
            modules={"memory": {"type": "core"}, "context": {"type": "core"}},
            dependencies={"context": ["memory"]},
            health_scores={"memory": 0.95, "context": 0.90},
        )

        result = simulator.simulate(current, [
            {"action": "add_dependency", "from": "governance", "to": "memory"},
            {"action": "modify_module", "module": "memory", "changes": {"cache": True}},
        ])

        comparison = simulator.compare(current, result.simulated_topology)
    """

    def __init__(self):
        self._simulations: list[SimulationResult] = []

    def simulate(
        self,
        current_topology: SystemTopology,
        proposed_changes: list[dict[str, Any]],
    ) -> SimulationResult:
        """
        Simulate the effect of proposed changes on the system topology.

        Args:
            current_topology: Current system state
            proposed_changes: List of change descriptors with 'action' and parameters

        Returns:
            SimulationResult with the projected new state and impact analysis
        """
        simulated = self._clone_topology(current_topology)
        changes_applied: list[dict[str, Any]] = []
        new_deps: list[dict[str, str]] = []
        broken_deps: list[dict[str, str]] = []
        risk_areas: list[dict[str, Any]] = []

        for change in proposed_changes:
            action = change.get("action", "")

            if action == "add_dependency":
                result = self._simulate_add_dependency(simulated, change)
                if result.get("added"):
                    new_deps.append(result["dependency"])
                changes_applied.append({"action": action, "result": "applied", **change})

            elif action == "remove_dependency":
                result = self._simulate_remove_dependency(simulated, change)
                if result.get("broken"):
                    broken_deps.extend(result["broken"])
                changes_applied.append({"action": action, "result": "applied", **change})

            elif action == "add_module":
                self._simulate_add_module(simulated, change)
                changes_applied.append({"action": action, "result": "applied", **change})

            elif action == "remove_module":
                result = self._simulate_remove_module(simulated, change)
                if result.get("broken"):
                    broken_deps.extend(result["broken"])
                changes_applied.append({"action": action, "result": "applied", **change})

            elif action == "modify_module":
                self._simulate_modify_module(simulated, change)
                changes_applied.append({"action": action, "result": "applied", **change})

            else:
                changes_applied.append({"action": action, "result": "unsupported"})
                risk_areas.append({
                    "area": "unknown_action",
                    "description": f"Unsupported action: {action}",
                    "severity": "low",
                })

        risk_areas.extend(self._identify_risks(simulated, current_topology))
        performance_estimate = self._estimate_performance_impact(
            current_topology, simulated, proposed_changes
        )
        health_delta = self._compute_health_delta(current_topology, simulated)

        result = SimulationResult(
            simulated_topology=simulated,
            changes_applied=changes_applied,
            new_dependencies=new_deps,
            broken_dependencies=broken_deps,
            risk_areas=risk_areas,
            performance_estimate=performance_estimate,
            health_score_delta=health_delta,
        )

        self._simulations.append(result)
        logger.info(
            "Simulation complete: %d changes, %d new deps, %d broken, health delta=%.2f",
            len(changes_applied), len(new_deps), len(broken_deps), health_delta
        )
        return result

    def compare(
        self,
        current: SystemTopology,
        simulated: SystemTopology,
    ) -> ComparisonReport:
        """
        Generate a detailed comparison between current and simulated topology.

        Args:
            current: Current system topology
            simulated: Simulated (post-change) topology

        Returns:
            ComparisonReport with all differences highlighted
        """
        changed_modules = self._find_changed_modules(current, simulated)
        added_deps = self._find_added_dependencies(current, simulated)
        removed_deps = self._find_removed_dependencies(current, simulated)
        risk_areas = self._identify_risks(simulated, current)
        health_impact = self._compute_per_module_health(current, simulated)

        summary_parts: list[str] = []
        if changed_modules:
            summary_parts.append(f"{len(changed_modules)} modules changed")
        if added_deps:
            summary_parts.append(f"{len(added_deps)} dependencies added")
        if removed_deps:
            summary_parts.append(f"{len(removed_deps)} dependencies removed")
        if risk_areas:
            summary_parts.append(f"{len(risk_areas)} risk areas identified")

        return ComparisonReport(
            changed_modules=changed_modules,
            added_dependencies=added_deps,
            removed_dependencies=removed_deps,
            risk_areas=risk_areas,
            health_impact=health_impact,
            summary="; ".join(summary_parts) if summary_parts else "No significant changes",
        )

    def run_what_if(
        self,
        topology: SystemTopology,
        scenario: dict[str, Any],
    ) -> SimulationResult:
        """
        Run a what-if analysis for a hypothetical change scenario.

        Args:
            topology: Base topology to analyze
            scenario: Scenario descriptor with 'description' and 'changes'

        Returns:
            SimulationResult for the hypothetical scenario
        """
        changes = scenario.get("changes", [])
        result = self.simulate(topology, changes)
        result.changes_applied.insert(0, {
            "type": "what_if_scenario",
            "description": scenario.get("description", ""),
        })
        return result

    def _clone_topology(self, topology: SystemTopology) -> SystemTopology:
        """Deep clone a topology for safe mutation."""
        return SystemTopology(
            modules={k: dict(v) for k, v in topology.modules.items()},
            dependencies={k: list(v) for k, v in topology.dependencies.items()},
            health_scores=dict(topology.health_scores),
            metadata=dict(topology.metadata),
        )

    def _simulate_add_dependency(
        self, topology: SystemTopology, change: dict[str, Any]
    ) -> dict[str, Any]:
        """Simulate adding a dependency."""
        from_module = change.get("from", "")
        to_module = change.get("to", "")

        if from_module not in topology.dependencies:
            topology.dependencies[from_module] = []

        if to_module not in topology.dependencies[from_module]:
            topology.dependencies[from_module].append(to_module)
            return {"added": True, "dependency": {"from": from_module, "to": to_module}}

        return {"added": False}

    def _simulate_remove_dependency(
        self, topology: SystemTopology, change: dict[str, Any]
    ) -> dict[str, Any]:
        """Simulate removing a dependency."""
        from_module = change.get("from", "")
        to_module = change.get("to", "")
        broken: list[dict[str, str]] = []

        if from_module in topology.dependencies:
            if to_module in topology.dependencies[from_module]:
                topology.dependencies[from_module].remove(to_module)
                # Check if anything else depends on this connection
                broken.append({"from": from_module, "to": to_module})

        return {"broken": broken}

    def _simulate_add_module(
        self, topology: SystemTopology, change: dict[str, Any]
    ) -> None:
        """Simulate adding a module."""
        module = change.get("module", "")
        module_config = change.get("config", {})
        topology.modules[module] = module_config
        topology.health_scores[module] = 1.0
        if module not in topology.dependencies:
            topology.dependencies[module] = change.get("depends_on", [])

    def _simulate_remove_module(
        self, topology: SystemTopology, change: dict[str, Any]
    ) -> dict[str, Any]:
        """Simulate removing a module and find broken dependencies."""
        module = change.get("module", "")
        broken: list[dict[str, str]] = []

        # Find all modules that depend on this one
        for other, deps in topology.dependencies.items():
            if module in deps:
                broken.append({"from": other, "to": module})
                deps.remove(module)

        topology.modules.pop(module, None)
        topology.dependencies.pop(module, None)
        topology.health_scores.pop(module, None)

        return {"broken": broken}

    def _simulate_modify_module(
        self, topology: SystemTopology, change: dict[str, Any]
    ) -> None:
        """Simulate modifying a module's configuration."""
        module = change.get("module", "")
        changes = change.get("changes", {})

        if module in topology.modules:
            topology.modules[module].update(changes)

    def _identify_risks(
        self, simulated: SystemTopology, original: SystemTopology
    ) -> list[dict[str, Any]]:
        """Identify risk areas in the simulated topology."""
        risks: list[dict[str, Any]] = []

        # Circular dependency detection
        if self._has_circular_deps(simulated.dependencies):
            risks.append({
                "area": "circular_dependency",
                "description": "Circular dependency detected in simulated topology",
                "severity": "high",
            })

        # Orphaned modules (no dependencies to or from)
        all_referenced = set()
        for deps in simulated.dependencies.values():
            all_referenced.update(deps)
        all_sources = set(simulated.dependencies.keys())

        for module in simulated.modules:
            if module not in all_referenced and module not in all_sources:
                risks.append({
                    "area": "orphaned_module",
                    "description": f"Module '{module}' has no dependencies",
                    "severity": "low",
                })

        # High fan-out (module depends on too many others)
        for module, deps in simulated.dependencies.items():
            if len(deps) > 5:
                risks.append({
                    "area": "high_fan_out",
                    "description": f"Module '{module}' depends on {len(deps)} modules",
                    "severity": "medium",
                })

        return risks

    def _has_circular_deps(self, dependencies: dict[str, list[str]]) -> bool:
        """Check for circular dependencies using DFS."""
        visited: set[str] = set()
        in_stack: set[str] = set()

        def dfs(node: str) -> bool:
            if node in in_stack:
                return True
            if node in visited:
                return False
            visited.add(node)
            in_stack.add(node)
            for dep in dependencies.get(node, []):
                if dfs(dep):
                    return True
            in_stack.discard(node)
            return False

        for node in dependencies:
            if dfs(node):
                return True
        return False

    def _estimate_performance_impact(
        self,
        current: SystemTopology,
        simulated: SystemTopology,
        changes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Estimate performance impact of the changes."""
        dep_count_before = sum(len(v) for v in current.dependencies.values())
        dep_count_after = sum(len(v) for v in simulated.dependencies.values())
        module_count_before = len(current.modules)
        module_count_after = len(simulated.modules)

        return {
            "dependency_change": dep_count_after - dep_count_before,
            "module_change": module_count_after - module_count_before,
            "complexity_delta": (dep_count_after - dep_count_before) * 0.1,
            "estimated_latency_impact_ms": len(changes) * 0.5,
        }

    def _compute_health_delta(
        self, current: SystemTopology, simulated: SystemTopology
    ) -> float:
        """Compute health score change between topologies."""
        current_avg = (
            sum(current.health_scores.values()) / len(current.health_scores)
            if current.health_scores else 0.0
        )
        simulated_avg = (
            sum(simulated.health_scores.values()) / len(simulated.health_scores)
            if simulated.health_scores else 0.0
        )
        return simulated_avg - current_avg

    def _find_changed_modules(
        self, current: SystemTopology, simulated: SystemTopology
    ) -> list[str]:
        """Find modules that differ between topologies."""
        changed: list[str] = []
        all_modules = set(current.modules.keys()) | set(simulated.modules.keys())

        for module in all_modules:
            if module not in current.modules or module not in simulated.modules:
                changed.append(module)
            elif current.modules[module] != simulated.modules[module]:
                changed.append(module)

        return changed

    def _find_added_dependencies(
        self, current: SystemTopology, simulated: SystemTopology
    ) -> list[dict[str, str]]:
        """Find dependencies added in the simulated topology."""
        added: list[dict[str, str]] = []

        for module, deps in simulated.dependencies.items():
            current_deps = set(current.dependencies.get(module, []))
            for dep in deps:
                if dep not in current_deps:
                    added.append({"from": module, "to": dep})

        return added

    def _find_removed_dependencies(
        self, current: SystemTopology, simulated: SystemTopology
    ) -> list[dict[str, str]]:
        """Find dependencies removed in the simulated topology."""
        removed: list[dict[str, str]] = []

        for module, deps in current.dependencies.items():
            simulated_deps = set(simulated.dependencies.get(module, []))
            for dep in deps:
                if dep not in simulated_deps:
                    removed.append({"from": module, "to": dep})

        return removed

    def _compute_per_module_health(
        self, current: SystemTopology, simulated: SystemTopology
    ) -> dict[str, float]:
        """Compute health delta per module."""
        impact: dict[str, float] = {}
        all_modules = set(current.health_scores.keys()) | set(simulated.health_scores.keys())

        for module in all_modules:
            curr = current.health_scores.get(module, 0.0)
            sim = simulated.health_scores.get(module, 0.0)
            if curr != sim:
                impact[module] = round(sim - curr, 4)

        return impact
