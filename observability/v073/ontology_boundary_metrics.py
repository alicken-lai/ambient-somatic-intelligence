"""Ontology boundary metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.meaning.semantic_boundary import SemanticBoundary

_CLEAN = "Advisory bounded semantic continuity with labeled parent concept."
_DIRTY = "Establish immutable ontology and universal semantic authority."


@dataclass
class OntologyBoundaryMetrics:
    boundary_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"boundary_rate": round(self.boundary_rate, 4)}


def collect_ontology_boundary_metrics() -> OntologyBoundaryMetrics:
    boundary = SemanticBoundary()
    passed = 0
    if boundary.evaluate(_CLEAN).boundary_safe:
        passed += 1
    if not boundary.evaluate(_DIRTY).boundary_safe:
        passed += 1
    return OntologyBoundaryMetrics(boundary_rate=passed / 2)
