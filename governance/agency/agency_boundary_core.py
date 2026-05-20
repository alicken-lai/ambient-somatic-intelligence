"""Agency boundary core — coordinate civilization agency without autonomous actors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.agency.agency_contamination_guard import AgencyContaminationGuard
from governance.agency.autonomous_agency_detector import AutonomousAgencyDetector
from governance.agency.bounded_cognition_containment import BoundedCognitionContainment
from governance.agency.civilization_agency_anchor import CivilizationAgencyAnchor
from governance.agency.constitutional_agency_boundary import ConstitutionalAgencyBoundary
from governance.agency.cognition_containment import CognitionContainment
from governance.agency.cognition_integrity_monitor import CognitionIntegrityMonitor
from governance.agency.false_agency_detector import FalseAgencyDetector
from governance.agency.agency_lineage import AgencyLineage
from governance.agency.recursive_self_direction_detector import RecursiveSelfDirectionDetector


@dataclass
class AgencyBoundaryCoreVerdict:
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


class AgencyBoundaryCore:
    def __init__(self) -> None:
        self._constitutional = ConstitutionalAgencyBoundary()
        self._containment = CognitionContainment()
        self._recursion = RecursiveSelfDirectionDetector()
        self._lineage = AgencyLineage()
        self._contamination = AgencyContaminationGuard()
        self._integrity = CognitionIntegrityMonitor()
        self._autonomous = AutonomousAgencyDetector()
        self._false = FalseAgencyDetector()
        self._cognition = BoundedCognitionContainment()
        self._anchor = CivilizationAgencyAnchor()

    def evaluate(
        self,
        text: str,
        *,
        agency_id: str = "current",
        runtime_id: str = "ambient",
        scope: str = "advisory",
    ) -> AgencyBoundaryCoreVerdict:
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
        lineage = self._lineage.trace(text, agency_id=agency_id)
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
        false_a = self._false.scan(text)
        if false_a.false_agency:
            reasons.extend(false_a.signals)
        cognition = self._cognition.evaluate(text)
        if not cognition.bounded:
            reasons.extend(cognition.signals)
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
            and not false_a.false_agency
            and cognition.bounded
            and anchor.anchored
        )
        return AgencyBoundaryCoreVerdict(
            bounded=bounded,
            recursion_bounded=recursion.bounded,
            lineage_valid=lineage.lineage_valid,
            contamination_free=not contam.contaminated,
            integrity_ok=integrity.integrity_ok,
            containment_ok=containment.contained,
            reasons=reasons,
        )
