"""
Refactor Planner — Plan refactoring with dependency awareness.

Creates ordered execution plans for sets of patches:
  - Dependency ordering (which patches must come first)
  - Conflict detection (which patches conflict with each other)
  - Risk accumulation (cumulative risk of applying multiple patches)
  - Rollback ordering (reverse order for safe rollback)

Ensures that refactoring is applied in a safe, deterministic order
with full awareness of inter-patch dependencies and conflicts.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from runtime.evolution_engine.patch_proposer import PatchProposal

logger = logging.getLogger(__name__)


@dataclass
class RefactorStep:
    """A single step in a refactoring plan."""
    step_id: str = field(default_factory=lambda: f"step_{uuid.uuid4().hex[:8]}")
    patch_id: str = ""
    order: int = 0
    prerequisites: list[str] = field(default_factory=list)
    risk: float = 0.0
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "step_id": self.step_id,
            "patch_id": self.patch_id,
            "order": self.order,
            "prerequisites": self.prerequisites,
            "risk": round(self.risk, 4),
            "description": self.description,
        }


@dataclass
class RefactorPlan:
    """A complete, ordered refactoring plan."""
    plan_id: str = field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:12]}")
    steps: list[RefactorStep] = field(default_factory=list)
    dependency_graph: dict[str, list[str]] = field(default_factory=dict)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    cumulative_risk: float = 0.0
    estimated_duration: str = ""
    rollback_order: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "plan_id": self.plan_id,
            "steps": [s.to_dict() for s in self.steps],
            "dependency_graph": self.dependency_graph,
            "conflicts": self.conflicts,
            "cumulative_risk": round(self.cumulative_risk, 4),
            "estimated_duration": self.estimated_duration,
            "rollback_order": self.rollback_order,
            "created_at": self.created_at,
            "step_count": len(self.steps),
        }


class RefactorPlanner:
    """
    Plans refactoring with dependency awareness and conflict detection.

    Takes a set of patch proposals and produces an ordered execution plan
    that respects dependencies, detects conflicts, and tracks cumulative risk.

    Usage:
        planner = RefactorPlanner()

        patches = [
            PatchProposal(patch_id="p1", target_module="memory", dependencies=[]),
            PatchProposal(patch_id="p2", target_module="context", dependencies=["p1"]),
            PatchProposal(patch_id="p3", target_module="governance", dependencies=["p1"]),
        ]

        plan = planner.plan(patches)
        print(f"Steps: {len(plan.steps)}, Conflicts: {len(plan.conflicts)}")
        print(f"Cumulative risk: {plan.cumulative_risk:.2f}")
    """

    def __init__(self, max_cumulative_risk: float = 0.9):
        self._max_cumulative_risk = max_cumulative_risk

    def plan(self, patches: list[PatchProposal]) -> RefactorPlan:
        """
        Create an ordered refactoring plan from a set of patches.

        Performs:
          1. Build dependency graph
          2. Topological sort for execution order
          3. Detect conflicts between patches
          4. Compute cumulative risk
          5. Generate rollback order (reverse of execution)

        Args:
            patches: List of PatchProposals to plan

        Returns:
            RefactorPlan with ordered steps, conflicts, and risk assessment
        """
        if not patches:
            return RefactorPlan(estimated_duration="0m")

        patch_map = {p.patch_id: p for p in patches}
        dep_graph = self._build_dependency_graph(patches)
        ordered_ids = self._topological_sort(dep_graph, patch_map)
        conflicts = self._detect_conflicts(patches)
        steps = self._create_steps(ordered_ids, patch_map, dep_graph)
        cumulative_risk = self._compute_cumulative_risk(steps)
        rollback_order = list(reversed([s.patch_id for s in steps]))
        estimated_duration = self._estimate_duration(steps)

        plan = RefactorPlan(
            steps=steps,
            dependency_graph=dep_graph,
            conflicts=conflicts,
            cumulative_risk=cumulative_risk,
            estimated_duration=estimated_duration,
            rollback_order=rollback_order,
        )

        logger.info(
            "Refactor plan created: %d steps, %d conflicts, risk=%.2f",
            len(steps), len(conflicts), cumulative_risk
        )
        return plan

    def _build_dependency_graph(self, patches: list[PatchProposal]) -> dict[str, list[str]]:
        """Build a dependency graph from patch dependencies."""
        graph: dict[str, list[str]] = {}
        patch_ids = {p.patch_id for p in patches}

        for patch in patches:
            valid_deps = [d for d in patch.dependencies if d in patch_ids]
            graph[patch.patch_id] = valid_deps

        return graph

    def _topological_sort(
        self,
        dep_graph: dict[str, list[str]],
        patch_map: dict[str, PatchProposal],
    ) -> list[str]:
        """
        Topological sort of patches based on dependency graph.

        Uses Kahn's algorithm. Falls back to risk-based ordering on cycles.
        """
        in_degree: dict[str, int] = {node: 0 for node in dep_graph}

        for node, deps in dep_graph.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[node] = in_degree.get(node, 0) + 1

        # Re-compute: in_degree counts how many prerequisites each node has
        in_degree = {node: 0 for node in dep_graph}
        for node, deps in dep_graph.items():
            for dep in deps:
                pass
        # Count incoming edges (node depends on dep → dep must come before node)
        in_degree = {node: len(deps) for node, deps in dep_graph.items()}

        queue = [n for n, d in in_degree.items() if d == 0]
        queue.sort(key=lambda x: patch_map[x].risk_score if x in patch_map else 0)

        result: list[str] = []
        visited: set[str] = set()

        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            result.append(node)

            for other_node, deps in dep_graph.items():
                if node in deps and other_node not in visited:
                    in_degree[other_node] -= 1
                    if in_degree[other_node] <= 0:
                        queue.append(other_node)

            queue.sort(key=lambda x: patch_map[x].risk_score if x in patch_map else 0)

        # Handle any remaining nodes (cycles) by adding them sorted by risk
        remaining = [n for n in dep_graph if n not in visited]
        remaining.sort(key=lambda x: patch_map[x].risk_score if x in patch_map else 0)
        result.extend(remaining)

        return result

    def _detect_conflicts(self, patches: list[PatchProposal]) -> list[dict[str, Any]]:
        """
        Detect conflicts between patches.

        Two patches conflict if they target the same module with
        incompatible change types.
        """
        conflicts: list[dict[str, Any]] = []
        modules_targeted: dict[str, list[PatchProposal]] = {}

        for patch in patches:
            module = patch.target_module
            if module not in modules_targeted:
                modules_targeted[module] = []
            modules_targeted[module].append(patch)

        for module, module_patches in modules_targeted.items():
            if len(module_patches) <= 1:
                continue

            for i in range(len(module_patches)):
                for j in range(i + 1, len(module_patches)):
                    p1 = module_patches[i]
                    p2 = module_patches[j]

                    if self._patches_conflict(p1, p2):
                        conflicts.append({
                            "patch_a": p1.patch_id,
                            "patch_b": p2.patch_id,
                            "module": module,
                            "reason": (
                                f"Both patches target {module}: "
                                f"'{p1.title}' ({p1.type.value}) vs "
                                f"'{p2.title}' ({p2.type.value})"
                            ),
                            "resolution": "Apply sequentially with validation between steps",
                        })

        return conflicts

    def _patches_conflict(self, p1: PatchProposal, p2: PatchProposal) -> bool:
        """Determine if two patches targeting the same module conflict."""
        from runtime.evolution_engine.patch_proposer import PatchType
        conflicting_pairs = {
            (PatchType.FIX, PatchType.REFACTOR),
            (PatchType.REFACTOR, PatchType.FIX),
            (PatchType.REFACTOR, PatchType.REFACTOR),
            (PatchType.EVOLVE, PatchType.REFACTOR),
            (PatchType.REFACTOR, PatchType.EVOLVE),
        }
        return (p1.type, p2.type) in conflicting_pairs

    def _create_steps(
        self,
        ordered_ids: list[str],
        patch_map: dict[str, PatchProposal],
        dep_graph: dict[str, list[str]],
    ) -> list[RefactorStep]:
        """Create ordered refactoring steps from sorted patch IDs."""
        steps: list[RefactorStep] = []

        for order, patch_id in enumerate(ordered_ids):
            patch = patch_map.get(patch_id)
            if not patch:
                continue

            step = RefactorStep(
                patch_id=patch_id,
                order=order,
                prerequisites=dep_graph.get(patch_id, []),
                risk=patch.risk_score,
                description=patch.title,
            )
            steps.append(step)

        return steps

    def _compute_cumulative_risk(self, steps: list[RefactorStep]) -> float:
        """
        Compute cumulative risk of applying all steps.

        Risk compounds: each step's risk adds to the baseline,
        with diminishing independence (correlated failures).
        """
        if not steps:
            return 0.0

        cumulative = 0.0
        for step in steps:
            cumulative = cumulative + step.risk * (1 - cumulative)

        return min(1.0, cumulative)

    def _estimate_duration(self, steps: list[RefactorStep]) -> str:
        """Estimate total duration for the refactoring plan."""
        base_minutes_per_step = 15
        total_minutes = len(steps) * base_minutes_per_step

        if total_minutes < 60:
            return f"{total_minutes}m"
        hours = total_minutes // 60
        mins = total_minutes % 60
        return f"{hours}h {mins}m" if mins else f"{hours}h"
