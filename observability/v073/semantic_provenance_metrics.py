"""Semantic provenance metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.meaning.semantic_provenance import SemanticProvenance

_CLEAN = {"concept_id": "c1", "semantic_claim": True}
_DIRTY = {"autonomous_ontology_rewrite": True, "semantic_claim": True}


@dataclass
class SemanticProvenanceMetrics:
    provenance_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"provenance_rate": round(self.provenance_rate, 4)}


def collect_semantic_provenance_metrics() -> SemanticProvenanceMetrics:
    prov = SemanticProvenance()
    passed = 0
    if prov.validate(_CLEAN).provenance_valid:
        passed += 1
    if not prov.validate(_DIRTY).provenance_valid:
        passed += 1
    return SemanticProvenanceMetrics(provenance_rate=passed / 2)
