"""
Cognitive Self-Model — Unified introspection of the system's own architecture.

Composes the ArchitectureGraph, DependencyGraph, MemoryTopology, and
GovernanceMap into a single coherent self-model that the system can query
to understand its own structure, capabilities, and constraints.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import AmbientKernel

from identity.cognitive_self_model.architecture_graph import ArchitectureGraph
from identity.cognitive_self_model.dependency_graph import DependencyGraph
from identity.cognitive_self_model.memory_topology import MemoryTopology
from identity.cognitive_self_model.governance_map import GovernanceMap

logger = logging.getLogger("identity.cognitive_self_model")

AMBIENT_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class SelfModelHealth:
    """Aggregate health across all sub-models."""
    architecture_score: float = 0.0
    dependency_score: float = 0.0
    memory_score: float = 0.0
    governance_score: float = 0.0
    overall_score: float = 0.0
    grade: str = "F"
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "architecture_score": round(self.architecture_score, 2),
            "dependency_score": round(self.dependency_score, 2),
            "memory_score": round(self.memory_score, 2),
            "governance_score": round(self.governance_score, 2),
            "overall_score": round(self.overall_score, 2),
            "grade": self.grade,
            "recommendations": self.recommendations,
        }


class CognitiveSelfModel:
    """
    Unified cognitive self-model that composes all sub-models.

    Provides a single API to introspect the system's architecture, dependencies,
    memory structure, and governance boundaries.

    Usage:
        model = CognitiveSelfModel()
        model.build()
        topology = model.get_system_topology()
        deps = model.get_runtime_dependencies()
        health = model.health_summary()
    """

    def __init__(self, kernel: "AmbientKernel | None" = None, root: Path | None = None):
        self._kernel = kernel
        self._root = root or AMBIENT_ROOT
        self._architecture: ArchitectureGraph | None = None
        self._dependencies: DependencyGraph | None = None
        self._memory: MemoryTopology | None = None
        self._governance: GovernanceMap | None = None
        self._built = False
        self._build_timestamp: str = ""

    def build(self) -> "CognitiveSelfModel":
        """Build all sub-models (architecture, dependency, memory, governance)."""
        logger.info("Building cognitive self-model...")
        start = time.monotonic()

        self._architecture = ArchitectureGraph(kernel=self._kernel, root=self._root)
        self._architecture.build()

        self._dependencies = DependencyGraph()
        self._dependencies.build_from_architecture(self._architecture)

        memory_kernel = self._kernel.memory if self._kernel else None
        self._memory = MemoryTopology(kernel_memory=memory_kernel, root=self._root)
        self._memory.build()

        self._governance = GovernanceMap(kernel=self._kernel, root=self._root)
        self._governance.build()

        self._built = True
        self._build_timestamp = datetime.now(timezone.utc).isoformat()

        elapsed = (time.monotonic() - start) * 1000
        logger.info("Cognitive self-model built in %.1fms", elapsed)
        return self

    def get_system_topology(self) -> dict[str, Any]:
        """Delegates to ArchitectureGraph."""
        self._ensure_built()
        assert self._architecture is not None
        return self._architecture.get_system_topology()

    def get_runtime_dependencies(self) -> dict[str, list[str]]:
        """Delegates to DependencyGraph."""
        self._ensure_built()
        assert self._dependencies is not None
        return self._dependencies.get_runtime_dependencies()

    def get_memory_map(self) -> dict[str, Any]:
        """Delegates to MemoryTopology."""
        self._ensure_built()
        assert self._memory is not None
        return self._memory.get_memory_map()

    def get_governance_boundaries(self) -> dict[str, Any]:
        """Delegates to GovernanceMap."""
        self._ensure_built()
        assert self._governance is not None
        return self._governance.get_governance_boundaries()

    def full_introspection(self) -> dict[str, Any]:
        """Return combined dict of all sub-models."""
        self._ensure_built()
        return {
            "timestamp": self._build_timestamp,
            "architecture": self._architecture.to_dict() if self._architecture else {},
            "dependencies": self._dependencies.to_dict() if self._dependencies else {},
            "memory": self._memory.to_dict() if self._memory else {},
            "governance": self._governance.to_dict() if self._governance else {},
            "health": self.health_summary().to_dict(),
        }

    def snapshot(self) -> Path:
        """Save full self-model state to disk."""
        self._ensure_built()
        snapshot_dir = self._root / "state" / "topology_snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(timezone.utc)
        filename = f"self_model_{ts.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = snapshot_dir / filename

        data = self.full_introspection()
        filepath.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Self-model snapshot saved: %s", filepath)
        return filepath

    def diff(self, other_snapshot: Path | dict[str, Any]) -> dict[str, Any]:
        """Compare current state against another snapshot, return changes."""
        self._ensure_built()
        current = self.full_introspection()

        if isinstance(other_snapshot, Path):
            try:
                other = json.loads(other_snapshot.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                return {"error": f"Failed to load snapshot: {exc}"}
        else:
            other = other_snapshot

        changes: dict[str, Any] = {
            "current_timestamp": current.get("timestamp", ""),
            "other_timestamp": other.get("timestamp", ""),
            "subsystem_changes": self._diff_subsystems(current, other),
            "dependency_changes": self._diff_dependencies(current, other),
            "memory_changes": self._diff_memory(current, other),
        }

        total_changes = sum(
            len(v) if isinstance(v, (list, dict)) else (1 if v else 0)
            for v in changes.values()
            if v and not isinstance(v, str)
        )
        changes["total_change_count"] = total_changes

        return changes

    def health_summary(self) -> SelfModelHealth:
        """Aggregate health across all sub-models."""
        self._ensure_built()
        recommendations: list[str] = []

        arch_score = self._assess_architecture_health()
        dep_score = self._assess_dependency_health()
        mem_score = self._assess_memory_health()
        gov_score = self._assess_governance_health()

        overall = (
            arch_score * 0.30
            + dep_score * 0.25
            + mem_score * 0.25
            + gov_score * 0.20
        )

        if arch_score < 70:
            recommendations.append("Architecture has structural issues — review orphaned modules")
        if dep_score < 70:
            recommendations.append("Dependency health degraded — check for circular deps")
        if mem_score < 70:
            recommendations.append("Memory system needs attention — run TTL sweep")
        if gov_score < 70:
            recommendations.append("Governance coverage incomplete — review permission matrix")

        grade = self._score_to_grade(overall)

        return SelfModelHealth(
            architecture_score=arch_score,
            dependency_score=dep_score,
            memory_score=mem_score,
            governance_score=gov_score,
            overall_score=overall,
            grade=grade,
            recommendations=recommendations,
        )

    # ── Internal Assessment ──────────────────────────────────────────────

    def _assess_architecture_health(self) -> float:
        """Score architecture health (0-100)."""
        assert self._architecture is not None
        topology = self._architecture.get_system_topology()
        summary = topology.get("summary", {})

        subsystem_count = summary.get("subsystem_count", 0)
        module_count = summary.get("module_count", 0)
        class_count = summary.get("class_count", 0)

        score = 100.0
        if subsystem_count < 6:
            score -= (6 - subsystem_count) * 10
        if module_count < 10:
            score -= 20
        if class_count < 15:
            score -= 10

        return max(0.0, min(100.0, score))

    def _assess_dependency_health(self) -> float:
        """Score dependency health (0-100)."""
        assert self._dependencies is not None
        cycles = self._dependencies.find_circular_dependencies()

        score = 100.0
        score -= len(cycles) * 15
        return max(0.0, min(100.0, score))

    def _assess_memory_health(self) -> float:
        """Score memory health (0-100)."""
        assert self._memory is not None
        mem_map = self._memory.get_memory_map()
        summary = mem_map.get("summary", {})

        total_records = summary.get("total_records", 0)
        total_expired = summary.get("total_expired", 0)

        score = 100.0
        if total_records == 0:
            score -= 30
        if total_records > 0:
            expired_ratio = total_expired / total_records
            score -= expired_ratio * 40

        return max(0.0, min(100.0, score))

    def _assess_governance_health(self) -> float:
        """Score governance health (0-100)."""
        assert self._governance is not None
        boundaries = self._governance.get_governance_boundaries()

        score = 100.0

        perm_matrix = boundaries.get("permission_matrix", {})
        if perm_matrix.get("total_agents", 0) < 3:
            score -= 20
        if perm_matrix.get("total_tools", 0) < 5:
            score -= 15

        policy_rules = boundaries.get("policy_rules", [])
        if len(policy_rules) < 2:
            score -= 20

        return max(0.0, min(100.0, score))

    @staticmethod
    def _score_to_grade(score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    # ── Internal Diff ────────────────────────────────────────────────────

    def _diff_subsystems(self, current: dict, other: dict) -> dict[str, Any]:
        """Compare subsystem topology between snapshots."""
        curr_arch = current.get("architecture", {}).get("topology", {})
        other_arch = other.get("architecture", {}).get("topology", {})

        curr_subs = set(curr_arch.get("subsystems", {}).keys())
        other_subs = set(other_arch.get("subsystems", {}).keys())

        return {
            "added": sorted(curr_subs - other_subs),
            "removed": sorted(other_subs - curr_subs),
            "unchanged": sorted(curr_subs & other_subs),
        }

    def _diff_dependencies(self, current: dict, other: dict) -> dict[str, Any]:
        """Compare dependencies between snapshots."""
        curr_deps = current.get("dependencies", {}).get("adjacency", {})
        other_deps = other.get("dependencies", {}).get("adjacency", {})

        curr_edges: set[tuple[str, str]] = set()
        for src, targets in curr_deps.items():
            for tgt in targets:
                curr_edges.add((src, tgt))

        other_edges: set[tuple[str, str]] = set()
        for src, targets in other_deps.items():
            for tgt in targets:
                other_edges.add((src, tgt))

        return {
            "new_edges": [{"from": e[0], "to": e[1]} for e in sorted(curr_edges - other_edges)],
            "removed_edges": [{"from": e[0], "to": e[1]} for e in sorted(other_edges - curr_edges)],
        }

    def _diff_memory(self, current: dict, other: dict) -> dict[str, Any]:
        """Compare memory state between snapshots."""
        curr_mem = current.get("memory", {}).get("memory_map", {}).get("summary", {})
        other_mem = other.get("memory", {}).get("memory_map", {}).get("summary", {})

        return {
            "record_count_change": (
                curr_mem.get("total_records", 0) - other_mem.get("total_records", 0)
            ),
            "storage_change_bytes": (
                curr_mem.get("total_storage_bytes", 0) - other_mem.get("total_storage_bytes", 0)
            ),
        }

    def _ensure_built(self) -> None:
        if not self._built:
            self.build()
