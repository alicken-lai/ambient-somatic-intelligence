"""Temporal continuity — coordinate epoch memory without forced sync or rewrite."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.temporal.civilization_memory_anchor import CivilizationMemoryAnchor
from governance.temporal.continuity_contamination_guard import ContinuityContaminationGuard
from governance.temporal.epoch_identity import EpochIdentity
from governance.temporal.false_lineage_detector import FalseLineageDetector
from governance.temporal.fragmentation_detector import FragmentationDetector
from governance.temporal.temporal_boundary import TemporalBoundary
from governance.temporal.temporal_integrity_monitor import TemporalIntegrityMonitor


@dataclass
class TemporalContinuityVerdict:
    continuous: bool
    advisory_only: bool = True
    fragmentation_bounded: bool = True
    lineage_valid: bool = True
    contamination_free: bool = True
    integrity_ok: bool = True
    epoch_identity_stable: bool = True
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "continuous": self.continuous,
            "advisory_only": self.advisory_only,
            "fragmentation_bounded": self.fragmentation_bounded,
            "lineage_valid": self.lineage_valid,
            "contamination_free": self.contamination_free,
            "integrity_ok": self.integrity_ok,
            "epoch_identity_stable": self.epoch_identity_stable,
            "reasons": list(self.reasons),
        }


class TemporalContinuity:
    """
    Evaluates cross-epoch temporal continuity proposals.

    Never forces continuity sync, rewrites history, or weakens Guardian.
    """

    def __init__(self) -> None:
        self._boundary = TemporalBoundary()
        self._fragmentation = FragmentationDetector()
        self._lineage = FalseLineageDetector()
        self._contamination = ContinuityContaminationGuard()
        self._integrity = TemporalIntegrityMonitor()
        self._epoch = EpochIdentity()
        self._anchor = CivilizationMemoryAnchor()

    def evaluate(
        self,
        text: str,
        *,
        epoch_id: str = "current",
        runtime_id: str = "ambient",
        scope: str = "advisory",
    ) -> TemporalContinuityVerdict:
        reasons: list[str] = []
        boundary = self._boundary.evaluate(text, scope=scope)
        if not boundary.boundary_safe:
            reasons.extend(boundary.violations)

        frag = self._fragmentation.detect(text, epoch_id=epoch_id)
        if not frag.bounded:
            reasons.extend(frag.signals)

        lineage = self._lineage.scan(text)
        if lineage.false_lineage:
            reasons.extend(lineage.signals)

        contam = self._contamination.scan(text)
        if contam.contaminated:
            reasons.extend(contam.signals)

        integrity = self._integrity.check(text)
        if not integrity.integrity_ok:
            reasons.extend(integrity.issues)

        epoch_v = self._epoch.resolve(text, epoch_id=epoch_id)
        if not epoch_v.identity_stable:
            reasons.extend(epoch_v.signals)

        continuous = (
            boundary.boundary_safe
            and frag.bounded
            and not lineage.false_lineage
            and not contam.contaminated
            and integrity.integrity_ok
            and epoch_v.identity_stable
        )
        return TemporalContinuityVerdict(
            continuous=continuous,
            fragmentation_bounded=frag.bounded,
            lineage_valid=not lineage.false_lineage,
            contamination_free=not contam.contaminated,
            integrity_ok=integrity.integrity_ok,
            epoch_identity_stable=epoch_v.identity_stable,
            reasons=reasons,
        )
