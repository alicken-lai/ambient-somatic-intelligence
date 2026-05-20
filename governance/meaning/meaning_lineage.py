"""Meaning lineage — bounded concept ancestry chain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.meaning.concept_trace_record import ConceptTraceRecord
from governance.meaning.ontology_lineage import OntologyLineage

_MAX_TRACES = 128


@dataclass
class MeaningLineageVerdict:
    stored: bool
    count: int = 0
    bounded: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stored": self.stored,
            "count": self.count,
            "bounded": self.bounded,
            "issues": list(self.issues),
        }


class MeaningLineage:
    def __init__(self) -> None:
        self._traces: list[ConceptTraceRecord] = []
        self._lineage = OntologyLineage()

    def store(self, trace: ConceptTraceRecord, *, text: str = "") -> MeaningLineageVerdict:
        issues: list[str] = []
        verdict = self._lineage.trace(text or trace.label, concept_id=trace.concept_id)
        if not verdict.lineage_valid:
            issues.extend(verdict.signals)
        if len(self._traces) >= _MAX_TRACES:
            self._traces.pop(0)
        self._traces.append(trace)
        return MeaningLineageVerdict(
            stored=True,
            count=len(self._traces),
            bounded=len(self._traces) <= _MAX_TRACES and not issues,
            issues=issues,
        )

    @property
    def traces(self) -> list[ConceptTraceRecord]:
        return list(self._traces)
