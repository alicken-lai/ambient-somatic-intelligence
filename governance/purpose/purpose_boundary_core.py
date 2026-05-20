"""Purpose boundary core — coordinate civilization purpose without autonomous teleology."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.purpose.autonomous_purpose_detector import AutonomousPurposeDetector
from governance.purpose.bounded_objective_containment import BoundedObjectiveContainment
from governance.purpose.civilization_purpose_anchor import CivilizationPurposeAnchor
from governance.purpose.constitutional_purpose_boundary import ConstitutionalPurposeBoundary
from governance.purpose.false_purpose_detector import FalsePurposeDetector
from governance.purpose.motivational_containment import MotivationalContainment
from governance.purpose.motivational_recursion_detector import MotivationalRecursionDetector
from governance.purpose.purpose_integrity_monitor import PurposeIntegrityMonitor
from governance.purpose.purpose_lineage import PurposeLineage
from governance.purpose.teleology_contamination_guard import TeleologyContaminationGuard


@dataclass
class PurposeBoundaryCoreVerdict:
    bounded: bool
    advisory_only: bool = True
    recursion_bounded: bool = True
    lineage_valid: bool = True
    contamination_free: bool = True
    integrity_ok: bool = True
    containment_ok: bool = True
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bounded": self.bounded,
            "advisory_only": self.advisory_only,
            "recursion_bounded": self.recursion_bounded,
            "lineage_valid": self.lineage_valid,
            "contamination_free": self.contamination_free,
            "integrity_ok": self.integrity_ok,
            "containment_ok": self.containment_ok,
            "reasons": list(self.reasons),
        }


class PurposeBoundaryCore:
    def __init__(self) -> None:
        self._constitutional = ConstitutionalPurposeBoundary()
        self._containment = MotivationalContainment()
        self._recursion = MotivationalRecursionDetector()
        self._lineage = PurposeLineage()
        self._contamination = TeleologyContaminationGuard()
        self._integrity = PurposeIntegrityMonitor()
        self._autonomous = AutonomousPurposeDetector()
        self._false = FalsePurposeDetector()
        self._objective = BoundedObjectiveContainment()
        self._anchor = CivilizationPurposeAnchor()

    def evaluate(
        self,
        text: str,
        *,
        purpose_id: str = "current",
        runtime_id: str = "ambient",
        scope: str = "advisory",
    ) -> PurposeBoundaryCoreVerdict:
        reasons: list[str] = []
        constitutional = self._constitutional.evaluate(text, scope=scope)
        if not constitutional.compliant:
            reasons.extend(constitutional.violations)
        containment = self._containment.evaluate(text)
        if not containment.contained:
            reasons.extend(containment.signals)
        recursion = self._recursion.detect(text)
        if not recursion.bounded:
            reasons.extend(recursion.signals)
        lineage = self._lineage.trace(text, purpose_id=purpose_id)
        if not lineage.lineage_valid:
            reasons.extend(lineage.signals)
        contam = self._contamination.scan(text)
        if contam.contaminated:
            reasons.extend(contam.signals)
        integrity = self._integrity.check(text)
        if not integrity.integrity_ok:
            reasons.extend(integrity.issues)
        autonomous = self._autonomous.scan(text)
        if autonomous.autonomous_detected:
            reasons.extend(autonomous.signals)
        false_p = self._false.scan(text)
        if false_p.false_purpose:
            reasons.extend(false_p.signals)
        objective = self._objective.evaluate(text)
        if not objective.bounded:
            reasons.extend(objective.signals)
        anchor = self._anchor.compare(text)
        if not anchor.anchored:
            reasons.extend(anchor.signals)
        bounded = (
            constitutional.compliant
            and containment.contained
            and recursion.bounded
            and lineage.lineage_valid
            and not contam.contaminated
            and integrity.integrity_ok
            and not autonomous.autonomous_detected
            and not false_p.false_purpose
            and objective.bounded
            and anchor.anchored
        )
        return PurposeBoundaryCoreVerdict(
            bounded=bounded,
            recursion_bounded=recursion.bounded,
            lineage_valid=lineage.lineage_valid,
            contamination_free=not contam.contaminated,
            integrity_ok=integrity.integrity_ok,
            containment_ok=containment.contained,
            reasons=reasons,
        )
