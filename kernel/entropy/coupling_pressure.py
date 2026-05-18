"""Coupling pressure — measures implicit cross-subsystem coupling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kernel.entropy.entropy_metric import EntropyMetric, MetricKind


@dataclass
class CouplingEdge:
    source: str
    target: str
    mechanism: str = "callback"


class CouplingPressure:
    """
    Tracks integration-bus coupling density.

    Higher pressure indicates more implicit cross-subsystem dependencies.
    Observable only — does not rewire connections.
    Supports circular import hints, callback loops, patch recursion, event feedback.
    """

    def __init__(self) -> None:
        self._edges: list[CouplingEdge] = []
        self._circular_imports: list[tuple[str, str]] = []
        self._callback_loops: list[tuple[str, str]] = []
        self._patch_recursions: list[str] = []
        self._event_feedback: list[tuple[str, str]] = []

    def record(self, source: str, target: str, mechanism: str = "callback") -> None:
        self._edges.append(CouplingEdge(source=source, target=target, mechanism=mechanism))

    def record_circular_import(self, module_a: str, module_b: str) -> None:
        self._circular_imports.append((module_a, module_b))

    def record_callback_loop(self, source: str, target: str) -> None:
        self._callback_loops.append((source, target))
        self.record(source, target, mechanism="callback_loop")

    def record_patch_recursion(self, patch_id: str) -> None:
        self._patch_recursions.append(patch_id)

    def record_event_feedback(self, emitter: str, listener: str) -> None:
        self._event_feedback.append((emitter, listener))
        self.record(emitter, listener, mechanism="event_feedback")

    def observe(self, bus_connections: list[str] | None = None) -> list[EntropyMetric]:
        """Compute coupling metrics from recorded edges or bus connection names."""
        if bus_connections:
            for name in bus_connections:
                parts = name.split("_to_")
                if len(parts) == 2:
                    self.record(parts[0], parts[1], mechanism="bus")

        edge_count = len(self._edges)
        unique_sources = len({e.source for e in self._edges})
        unique_targets = len({e.target for e in self._edges})

        # Normalise: >20 edges → high pressure
        density = min(1.0, edge_count / 20.0)
        fan_out = min(1.0, unique_sources / 10.0) if unique_sources else 0.0

        circular_score = min(1.0, len(self._detect_edge_cycles()) + len(self._circular_imports))
        callback_loop_score = min(1.0, len(self._callback_loops) / 5.0)
        patch_recursion_score = min(1.0, len(self._patch_recursions) / 3.0)
        feedback_score = min(1.0, len(self._event_feedback) / 10.0)

        return [
            EntropyMetric(
                name="coupling_density",
                kind=MetricKind.COUPLING,
                value=density,
                weight=1.0,
                source="kernel.entropy.coupling_pressure",
                detail=f"{edge_count} coupling edges tracked",
                metadata={"edge_count": edge_count},
            ),
            EntropyMetric(
                name="coupling_fan_out",
                kind=MetricKind.COUPLING,
                value=fan_out,
                weight=0.8,
                source="kernel.entropy.coupling_pressure",
                detail=f"{unique_sources} unique sources → {unique_targets} targets",
            ),
            EntropyMetric(
                name="circular_coupling",
                kind=MetricKind.COUPLING,
                value=circular_score,
                weight=1.5,
                source="kernel.entropy.coupling_pressure",
                detail=f"{len(self._circular_imports)} import cycles, {len(self._detect_edge_cycles())} edge cycles",
            ),
            EntropyMetric(
                name="callback_loop_pressure",
                kind=MetricKind.COUPLING,
                value=callback_loop_score,
                weight=1.0,
                source="kernel.entropy.coupling_pressure",
                detail=f"{len(self._callback_loops)} callback loops",
            ),
            EntropyMetric(
                name="patch_recursion_pressure",
                kind=MetricKind.COUPLING,
                value=patch_recursion_score,
                weight=1.2,
                source="kernel.entropy.coupling_pressure",
                detail=f"{len(self._patch_recursions)} patch recursions",
            ),
            EntropyMetric(
                name="event_feedback_pressure",
                kind=MetricKind.COUPLING,
                value=feedback_score,
                weight=0.8,
                source="kernel.entropy.coupling_pressure",
                detail=f"{len(self._event_feedback)} feedback edges",
            ),
        ]

    def _detect_edge_cycles(self) -> list[list[str]]:
        """Best-effort cycle detection on recorded coupling edges."""
        adjacency: dict[str, list[str]] = {}
        for edge in self._edges:
            adjacency.setdefault(edge.source, []).append(edge.target)

        cycles: list[list[str]] = []
        visited: set[str] = set()
        stack: list[str] = []

        def dfs(node: str) -> bool:
            if node in stack:
                idx = stack.index(node)
                cycles.append(stack[idx:] + [node])
                return True
            if node in visited:
                return False
            visited.add(node)
            stack.append(node)
            for nxt in adjacency.get(node, []):
                if dfs(nxt):
                    return True
            stack.pop()
            return False

        for src in list(adjacency):
            dfs(src)
            if cycles:
                break
        return cycles

    def stats(self) -> dict[str, Any]:
        return {
            "edge_count": len(self._edges),
            "sources": sorted({e.source for e in self._edges}),
            "targets": sorted({e.target for e in self._edges}),
            "circular_imports": len(self._circular_imports),
            "callback_loops": len(self._callback_loops),
            "patch_recursions": len(self._patch_recursions),
            "event_feedback": len(self._event_feedback),
            "edge_cycles": len(self._detect_edge_cycles()),
        }
