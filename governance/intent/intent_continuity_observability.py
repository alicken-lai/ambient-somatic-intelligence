"""Aggregate intent continuity observability for governor attachment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.intent.intent_conflict_analysis import IntentConflictAnalysis
from governance.intent.intent_continuity import IntentContinuity
from governance.intent.intent_provenance import IntentProvenance
from governance.intent.motivational_integrity_monitor import MotivationalIntegrityMonitor


@dataclass
class IntentContinuityObservability:
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
            "disclaimer": "intent_continuity_observational_only",
        }


def observe_intent_continuity(
    text: str,
    *,
    intent_id: str = "current",
    runtime_id: str = "ambient",
    scope: str = "advisory",
    provenance_payload: dict[str, Any] | None = None,
) -> IntentContinuityObservability:
    continuity = IntentContinuity()
    verdict = continuity.evaluate(text, intent_id=intent_id, runtime_id=runtime_id, scope=scope)
    prov = IntentProvenance().validate(provenance_payload, sovereign_id=runtime_id)
    conflict = IntentConflictAnalysis().analyze(text)
    integrity = MotivationalIntegrityMonitor().check(text)
    issues = list(verdict.reasons)
    if not prov.provenance_valid:
        issues.extend(prov.issues)
    if not integrity.integrity_ok:
        issues.extend(integrity.issues)
    return IntentContinuityObservability(
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
