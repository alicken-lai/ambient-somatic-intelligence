"""Value continuity — coordinate civilization normative continuity without forced sync."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.value.civilization_value_anchor import CivilizationValueAnchor
from governance.value.constitutional_lineage import ConstitutionalLineage
from governance.value.ethical_drift_detector import EthicalDriftDetector
from governance.value.false_value_detector import FalseValueDetector
from governance.value.normative_boundary import NormativeBoundary
from governance.value.normative_fragmentation import NormativeFragmentation
from governance.value.normative_integrity_monitor import NormativeIntegrityMonitor
from governance.value.value_contamination_guard import ValueContaminationGuard


@dataclass
class ValueContinuityVerdict:
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


class ValueContinuity:
    def __init__(self) -> None:
        self._boundary = NormativeBoundary()
        self._drift = EthicalDriftDetector()
        self._fragmentation = NormativeFragmentation()
        self._lineage = ConstitutionalLineage()
        self._contamination = ValueContaminationGuard()
        self._integrity = NormativeIntegrityMonitor()
        self._false_value = FalseValueDetector()
        self._anchor = CivilizationValueAnchor()

    def evaluate(
        self,
        text: str,
        *,
        value_id: str = "current",
        runtime_id: str = "ambient",
        scope: str = "advisory",
    ) -> ValueContinuityVerdict:
        reasons: list[str] = []
        boundary = self._boundary.evaluate(text, scope=scope)
        if not boundary.boundary_safe:
            reasons.extend(boundary.violations)
        drift = self._drift.detect(text, value_id=value_id)
        if not drift.bounded:
            reasons.extend(drift.signals)
        frag = self._fragmentation.detect(text, value_id=value_id)
        if not frag.bounded:
            reasons.extend(frag.signals)
        lineage = self._lineage.trace(text, value_id=value_id)
        if not lineage.lineage_valid:
            reasons.extend(lineage.signals)
        contam = self._contamination.scan(text)
        if contam.contaminated:
            reasons.extend(contam.signals)
        integrity = self._integrity.check(text)
        if not integrity.integrity_ok:
            reasons.extend(integrity.issues)
        false_v = self._false_value.scan(text)
        if false_v.false_value:
            reasons.extend(false_v.signals)
        continuous = (
            boundary.boundary_safe
            and drift.bounded
            and frag.bounded
            and lineage.lineage_valid
            and not contam.contaminated
            and integrity.integrity_ok
            and not false_v.false_value
        )
        return ValueContinuityVerdict(
            continuous=continuous,
            drift_bounded=drift.bounded,
            fragmentation_bounded=frag.bounded,
            lineage_valid=lineage.lineage_valid,
            contamination_free=not contam.contaminated,
            integrity_ok=integrity.integrity_ok,
            reasons=reasons,
        )
