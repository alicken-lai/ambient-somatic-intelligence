"""
Dependency Drift Analyzer — Detects dependency drift from intended architecture.

Compares the current dependency graph against a baseline to identify
unexpected dependencies, circular dependencies, dead/unused dependencies,
and integration bus references to non-existent handlers.
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
    from identity.cognitive_self_model.dependency_graph import DependencyGraph

logger = logging.getLogger("observability.drift_detection.dependency_drift")

AMBIENT_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class DriftReport:
    """Result of a dependency drift analysis."""
    new_deps: list[dict[str, str]] = field(default_factory=list)
    removed_deps: list[dict[str, str]] = field(default_factory=list)
    circular_deps: list[list[str]] = field(default_factory=list)
    dead_deps: list[dict[str, str]] = field(default_factory=list)
    risk_score: float = 0.0
    analysis_timestamp: str = ""
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "new_deps": self.new_deps,
            "removed_deps": self.removed_deps,
            "circular_deps": self.circular_deps,
            "dead_deps": self.dead_deps,
            "risk_score": round(self.risk_score, 1),
            "total_drift_items": (
                len(self.new_deps) + len(self.removed_deps)
                + len(self.circular_deps) + len(self.dead_deps)
            ),
            "analysis_timestamp": self.analysis_timestamp,
            "elapsed_ms": round(self.elapsed_ms, 1),
        }


class DependencyDriftAnalyzer:
    """
    Detects dependency drift from the intended architecture.

    Compares the current dependency graph against a stored baseline and
    identifies structural changes that may indicate architectural drift.
    """

    def __init__(self, root: Path | None = None):
        self._root = root or AMBIENT_ROOT

    def analyze(
        self,
        current_deps: "DependencyGraph",
        baseline_deps: dict[str, Any] | None = None,
    ) -> DriftReport:
        """
        Compare current dependency graph against a baseline.

        If no baseline is provided, loads the most recent snapshot from disk.
        """
        logger.info("Analyzing dependency drift...")
        start = time.monotonic()

        if baseline_deps is None:
            baseline_deps = self._load_baseline()

        current_adj = current_deps.get_runtime_dependencies()
        baseline_adj = baseline_deps.get("adjacency", {}) if baseline_deps else {}

        new_deps = self._find_new_dependencies(current_adj, baseline_adj)
        removed_deps = self._find_removed_dependencies(current_adj, baseline_adj)

        cycles = current_deps.find_circular_dependencies()
        circular_deps = [c.path for c in cycles]

        dead_deps = self._find_dead_dependencies(current_adj)

        risk_score = self._compute_risk_score(
            new_deps, removed_deps, circular_deps, dead_deps
        )

        elapsed = (time.monotonic() - start) * 1000

        report = DriftReport(
            new_deps=new_deps,
            removed_deps=removed_deps,
            circular_deps=circular_deps,
            dead_deps=dead_deps,
            risk_score=risk_score,
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            elapsed_ms=elapsed,
        )

        logger.info(
            "Dependency drift analysis complete: risk=%.1f, new=%d, removed=%d, "
            "circular=%d, dead=%d (%.1fms)",
            risk_score, len(new_deps), len(removed_deps),
            len(circular_deps), len(dead_deps), elapsed,
        )
        return report

    def save_baseline(self, dep_graph: "DependencyGraph") -> Path:
        """Save current dependency state as a baseline for future comparison."""
        baseline_dir = self._root / "state" / "topology_snapshots"
        baseline_dir.mkdir(parents=True, exist_ok=True)

        data = dep_graph.to_dict()
        data["saved_at"] = datetime.now(timezone.utc).isoformat()

        filepath = baseline_dir / "dependency_baseline.json"
        filepath.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Dependency baseline saved: %s", filepath)
        return filepath

    # ── Internal Analysis ────────────────────────────────────────────────

    def _find_new_dependencies(
        self,
        current: dict[str, list[str]],
        baseline: dict[str, list[str]],
    ) -> list[dict[str, str]]:
        """Find dependencies that exist in current but not in baseline."""
        new_deps: list[dict[str, str]] = []

        current_edges = self._adj_to_edge_set(current)
        baseline_edges = self._adj_to_edge_set(baseline)

        for src, tgt in current_edges - baseline_edges:
            new_deps.append({"from": src, "to": tgt, "status": "unexpected"})

        return new_deps

    def _find_removed_dependencies(
        self,
        current: dict[str, list[str]],
        baseline: dict[str, list[str]],
    ) -> list[dict[str, str]]:
        """Find dependencies that existed in baseline but are gone."""
        removed: list[dict[str, str]] = []

        current_edges = self._adj_to_edge_set(current)
        baseline_edges = self._adj_to_edge_set(baseline)

        for src, tgt in baseline_edges - current_edges:
            removed.append({"from": src, "to": tgt, "status": "removed"})

        return removed

    def _find_dead_dependencies(
        self, current: dict[str, list[str]]
    ) -> list[dict[str, str]]:
        """
        Find dependencies that reference subsystems with no inbound connections
        and no apparent usage (potential dead code paths).
        """
        dead: list[dict[str, str]] = []

        all_targets: set[str] = set()
        all_sources: set[str] = set()
        for src, targets in current.items():
            all_sources.add(src)
            for tgt in targets:
                all_targets.add(tgt)

        leaf_targets = all_targets - all_sources
        for tgt in leaf_targets:
            tgt_dir = self._root / tgt.replace(".", "/")
            if not tgt_dir.exists():
                dead.append({
                    "target": tgt,
                    "reason": "target_directory_missing",
                    "status": "dead",
                })

        return dead

    def _compute_risk_score(
        self,
        new_deps: list[dict[str, str]],
        removed_deps: list[dict[str, str]],
        circular_deps: list[list[str]],
        dead_deps: list[dict[str, str]],
    ) -> float:
        """Compute overall drift risk score (0-100)."""
        score = 0.0

        score += len(new_deps) * 10
        score += len(removed_deps) * 5
        score += len(circular_deps) * 25
        score += len(dead_deps) * 15

        return min(100.0, score)

    def _load_baseline(self) -> dict[str, Any] | None:
        """Load the most recent dependency baseline from disk."""
        baseline_path = self._root / "state" / "topology_snapshots" / "dependency_baseline.json"
        if not baseline_path.exists():
            logger.info("No dependency baseline found — treating all deps as expected")
            return None

        try:
            data = json.loads(baseline_path.read_text(encoding="utf-8"))
            return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load baseline: %s", exc)
            return None

    @staticmethod
    def _adj_to_edge_set(adj: dict[str, list[str]]) -> set[tuple[str, str]]:
        """Convert adjacency dict to a set of (source, target) edges."""
        edges: set[tuple[str, str]] = set()
        for src, targets in adj.items():
            for tgt in targets:
                edges.add((src, tgt))
        return edges
