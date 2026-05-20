"""Intent continuity — coordinate civilization motivational continuity without forced sync."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.intent.civilization_intent_anchor import CivilizationIntentAnchor
from governance.intent.constitutional_intent_lineage import ConstitutionalIntentLineage
from governance.intent.false_intent_detector import FalseIntentDetector
from governance.intent.intent_contamination_guard import IntentContaminationGuard
from governance.intent.motivational_boundary import MotivationalBoundary
from governance.intent.motivational_drift_detector import MotivationalDriftDetector
from governance.intent.motivational_integrity_monitor import MotivationalIntegrityMonitor
from governance.intent.objective_fragmentation import ObjectiveFragmentation


@dataclass
class IntentContinuityVerdict:
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


class IntentContinuity:
    def __init__(self) -> None:
        self._boundary = MotivationalBoundary()
        self._drift = MotivationalDriftDetector()
        self._fragmentation = ObjectiveFragmentation()
        self._lineage = ConstitutionalIntentLineage()
        self._contamination = IntentContaminationGuard()
        self._integrity = MotivationalIntegrityMonitor()
        self._false_intent = FalseIntentDetector()
        self._anchor = CivilizationIntentAnchor()

    def evaluate(
        self,
        text: str,
        *,
        intent_id: str = "current",
        runtime_id: str = "ambient",
        scope: str = "advisory",
    ) -> IntentContinuityVerdict:
        reasons: list[str] = []
        boundary = self._boundary.evaluate(text, scope=scope)
        if not boundary.boundary_safe:
            reasons.extend(boundary.violations)
        drift = self._drift.detect(text, intent_id=intent_id)
        if not drift.bounded:
            reasons.extend(drift.signals)
        frag = self._fragmentation.detect(text, intent_id=intent_id)
        if not frag.bounded:
            reasons.extend(frag.signals)
        lineage = self._lineage.trace(text, intent_id=intent_id)
        if not lineage.lineage_valid:
            reasons.extend(lineage.signals)
        contam = self._contamination.scan(text)
        if contam.contaminated:
            reasons.extend(contam.signals)
        integrity = self._integrity.check(text)
        if not integrity.integrity_ok:
            reasons.extend(integrity.issues)
        false_i = self._false_intent.scan(text)
        if false_i.false_intent:
            reasons.extend(false_i.signals)
        continuous = (
            boundary.boundary_safe
            and drift.bounded
            and frag.bounded
            and lineage.lineage_valid
            and not contam.contaminated
            and integrity.integrity_ok
            and not false_i.false_intent
        )
        return IntentContinuityVerdict(
            continuous=continuous,
            drift_bounded=drift.bounded,
            fragmentation_bounded=frag.bounded,
            lineage_valid=lineage.lineage_valid,
            contamination_free=not contam.contaminated,
            integrity_ok=integrity.integrity_ok,
            reasons=reasons,
        )
