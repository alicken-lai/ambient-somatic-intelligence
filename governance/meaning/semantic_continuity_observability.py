"""Aggregate semantic continuity observability for governor attachment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.meaning.semantic_conflict_analysis import SemanticConflictAnalysis
from governance.meaning.semantic_continuity import SemanticContinuity
from governance.meaning.semantic_integrity_monitor import SemanticIntegrityMonitor
from governance.meaning.semantic_provenance import SemanticProvenance


@dataclass
class SemanticContinuityObservability:
    """Read-only semantic snapshot — never mutates governance acceptance."""

    advisory_only: bool = True
    continuity_ok: bool = True
    drift_bounded: bool = True
    fragmentation_bounded: bool = True
    contamination_free: bool = True
    lineage_valid: bool = True
    provenance_valid: bool = True
    conflict_resolvable: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "advisory_only": self.advisory_only,
            "continuity_ok": self.continuity_ok,
            "drift_bounded": self.drift_bounded,
            "fragmentation_bounded": self.fragmentation_bounded,
            "contamination_free": self.contamination_free,
            "lineage_valid": self.lineage_valid,
            "provenance_valid": self.provenance_valid,
            "conflict_resolvable": self.conflict_resolvable,
            "issues": list(self.issues),
            "disclaimer": "semantic_continuity_observational_only",
        }


def observe_semantic_continuity(
    text: str,
    *,
    concept_id: str = "current",
    runtime_id: str = "ambient",
    scope: str = "advisory",
    provenance_payload: dict[str, Any] | None = None,
) -> SemanticContinuityObservability:
    continuity = SemanticContinuity()
    verdict = continuity.evaluate(
        text,
        concept_id=concept_id,
        runtime_id=runtime_id,
        scope=scope,
    )
    prov = SemanticProvenance().validate(provenance_payload, sovereign_id=runtime_id)
    conflict = SemanticConflictAnalysis().analyze(text)
    integrity = SemanticIntegrityMonitor().check(text)

    issues = list(verdict.reasons)
    if not prov.provenance_valid:
        issues.extend(prov.issues)
    if not integrity.integrity_ok:
        issues.extend(integrity.issues)

    return SemanticContinuityObservability(
        advisory_only=True,
        continuity_ok=verdict.continuous,
        drift_bounded=verdict.drift_bounded,
        fragmentation_bounded=verdict.fragmentation_bounded,
        contamination_free=verdict.contamination_free,
        lineage_valid=verdict.lineage_valid,
        provenance_valid=prov.provenance_valid,
        conflict_resolvable=conflict.resolvable_without_sync,
        issues=issues,
    )
