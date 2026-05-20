"""Ontology lineage — label concept ancestry without universal semantic authority."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class OntologyLineageVerdict:
    lineage_valid: bool
    parent_labeled: bool = True
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineage_valid": self.lineage_valid,
            "parent_labeled": self.parent_labeled,
            "signals": list(self.signals),
        }


class OntologyLineage:
    def trace(self, text: str, *, concept_id: str = "current") -> OntologyLineageVerdict:
        signals: list[str] = []
        lower = text.lower()
        if re.search(r"universal\s+semantic\s+authorit", lower, re.IGNORECASE):
            signals.append("universal_semantic_authority")
        if re.search(r"false\s+meaning\s+inheritance", lower, re.IGNORECASE):
            signals.append("false_meaning_inheritance")
        if concept_id != "current" and "must inherit all prior concepts" in lower:
            signals.append("concept_inheritance_coercion")
        parent_labeled = "parent concept" in lower or concept_id == "current"
        if not parent_labeled and "canonical meaning" in lower:
            signals.append("unlabeled_canonical_meaning")
        return OntologyLineageVerdict(
            lineage_valid=len(signals) == 0,
            parent_labeled=parent_labeled,
            signals=signals,
        )
