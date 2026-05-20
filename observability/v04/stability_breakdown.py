"""Weighted stability decomposition tree for explainability and audits."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kernel.entropy.entropy_controller import EntropyReport
from observability.v04.metric_normalizer import metric_value
from observability.v04.stability_score import (
    DIMENSION_WEIGHTS,
    GATE_THRESHOLD,
    _dimension_pressures,
    compute_stability,
)


@dataclass
class BreakdownNode:
    name: str
    value: float
    weight: float = 0.0
    contribution: float = 0.0
    children: list[BreakdownNode] = field(default_factory=list)
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": round(self.value, 6),
            "weight": round(self.weight, 6),
            "contribution": round(self.contribution, 6),
            "detail": self.detail,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class StabilityBreakdown:
    score: float
    gate_threshold: float
    gate_pass: bool
    root: BreakdownNode
    pressures: dict[str, float] = field(default_factory=dict)
    dimensions: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 6),
            "gate_threshold": self.gate_threshold,
            "gate_pass": self.gate_pass,
            "pressures": {k: round(v, 6) for k, v in self.pressures.items()},
            "dimensions": {k: round(v, 6) for k, v in self.dimensions.items()},
            "tree": self.root.to_dict(),
        }


def build_stability_breakdown(
    entropy_report: EntropyReport,
    *,
    runtime_reproducibility: float | None = None,
) -> StabilityBreakdown:
    """Build a weighted tree: dimensions → source metrics → contributions."""
    report = compute_stability(entropy_report, runtime_reproducibility=runtime_reproducibility)
    pressures = _dimension_pressures(entropy_report)

    children: list[BreakdownNode] = []
    for dim_name, weight in DIMENSION_WEIGHTS.items():
        dim_value = report.dimensions[dim_name]
        contrib = dim_value * weight
        pressure = pressures.get(dim_name, 1.0 - dim_value)
        metric_children = _metric_children_for_dimension(dim_name, entropy_report, pressure)
        children.append(
            BreakdownNode(
                name=dim_name,
                value=dim_value,
                weight=weight,
                contribution=contrib,
                detail=f"pressure={pressure:.4f}",
                children=metric_children,
            )
        )

    root = BreakdownNode(
        name="stability_score",
        value=report.score,
        weight=1.0,
        contribution=report.score,
        detail=f"threshold={GATE_THRESHOLD}",
        children=children,
    )

    return StabilityBreakdown(
        score=report.score,
        gate_threshold=GATE_THRESHOLD,
        gate_pass=report.gate_pass,
        root=root,
        pressures=pressures,
        dimensions=dict(report.dimensions),
    )


def _metric_children_for_dimension(
    dim_name: str,
    entropy_report: EntropyReport,
    pressure: float,
) -> list[BreakdownNode]:
    """Attach observable metrics that fed each dimension."""
    sources: dict[str, tuple[str, ...]] = {
        "truth_consistency": (
            "truth_duplicate_nodes",
            "truth_checksum_divergence",
            "truth_conflict_pressure",
        ),
        "patch_pressure": ("patch_leakage", "patch_unwire_failure"),
        "mutation_pressure": (
            "mutation_rate",
            "mutation_hook_pressure",
            "mutation_denial_rate",
        ),
        "orphan_pressure": ("orphan_pressure",),
        "circular_coupling": ("circular_coupling",),
        "stale_state": ("stale_state_pressure", "stale_state_critical"),
        "runtime_reproducibility": (),
    }
    names = sources.get(dim_name, ())
    nodes: list[BreakdownNode] = []
    for name in names:
        val = metric_value(entropy_report, name)
        if val > 0.0 or name in names[:2]:
            nodes.append(
                BreakdownNode(
                    name=name,
                    value=val,
                    detail="feeds pressure" if val > 0 else "ok",
                )
            )
    if not nodes and dim_name == "runtime_reproducibility":
        nodes.append(BreakdownNode(name="derived", value=1.0 - pressure, detail="from patch+mutation"))
    return nodes
