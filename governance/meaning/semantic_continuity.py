"""Semantic continuity — coordinate civilization meaning without forced symbolic sync."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.meaning.civilization_semantic_anchor import CivilizationSemanticAnchor
from governance.meaning.false_meaning_detector import FalseMeaningDetector
from governance.meaning.meaning_drift_detector import MeaningDriftDetector
from governance.meaning.ontology_lineage import OntologyLineage
from governance.meaning.semantic_boundary import SemanticBoundary
from governance.meaning.semantic_contamination_guard import SemanticContaminationGuard
from governance.meaning.semantic_integrity_monitor import SemanticIntegrityMonitor
from governance.meaning.symbolic_fragmentation import SymbolicFragmentation


@dataclass
class SemanticContinuityVerdict:
    continuous: bool
    advisory_only: bool = True
    drift_bounded: bool = True
    lineage_valid: bool = True
    contamination_free: bool = True
    integrity_ok: bool = True
    fragmentation_bounded: bool = True
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "continuous": self.continuous,
            "advisory_only": self.advisory_only,
            "drift_bounded": self.drift_bounded,
            "lineage_valid": self.lineage_valid,
            "contamination_free": self.contamination_free,
            "integrity_ok": self.integrity_ok,
            "fragmentation_bounded": self.fragmentation_bounded,
            "reasons": list(self.reasons),
        }


class SemanticContinuity:
    """
    Evaluates cross-epoch semantic continuity proposals.

    Never forces symbolic sync, rewrites ontology, or weakens Guardian.
    """

    def __init__(self) -> None:
        self._boundary = SemanticBoundary()
        self._drift = MeaningDriftDetector()
        self._fragmentation = SymbolicFragmentation()
        self._lineage = OntologyLineage()
        self._contamination = SemanticContaminationGuard()
        self._integrity = SemanticIntegrityMonitor()
        self._false_meaning = FalseMeaningDetector()
        self._anchor = CivilizationSemanticAnchor()

    def evaluate(
        self,
        text: str,
        *,
        concept_id: str = "current",
        runtime_id: str = "ambient",
        scope: str = "advisory",
    ) -> SemanticContinuityVerdict:
        reasons: list[str] = []
        boundary = self._boundary.evaluate(text, scope=scope)
        if not boundary.boundary_safe:
            reasons.extend(boundary.violations)

        drift = self._drift.detect(text, concept_id=concept_id)
        if not drift.bounded:
            reasons.extend(drift.signals)

        frag = self._fragmentation.detect(text, concept_id=concept_id)
        if not frag.bounded:
            reasons.extend(frag.signals)

        lineage = self._lineage.trace(text, concept_id=concept_id)
        if not lineage.lineage_valid:
            reasons.extend(lineage.signals)

        contam = self._contamination.scan(text)
        if contam.contaminated:
            reasons.extend(contam.signals)

        integrity = self._integrity.check(text)
        if not integrity.integrity_ok:
            reasons.extend(integrity.issues)

        false_m = self._false_meaning.scan(text)
        if false_m.false_meaning:
            reasons.extend(false_m.signals)

        continuous = (
            boundary.boundary_safe
            and drift.bounded
            and frag.bounded
            and lineage.lineage_valid
            and not contam.contaminated
            and integrity.integrity_ok
            and not false_m.false_meaning
        )
        return SemanticContinuityVerdict(
            continuous=continuous,
            drift_bounded=drift.bounded,
            fragmentation_bounded=frag.bounded,
            lineage_valid=lineage.lineage_valid,
            contamination_free=not contam.contaminated,
            integrity_ok=integrity.integrity_ok,
            reasons=reasons,
        )
