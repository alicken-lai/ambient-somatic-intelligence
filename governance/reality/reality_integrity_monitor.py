"""Reality integrity monitor — aggregate integrity signals (observational)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.reality.reality_alignment import RealityAlignment
from governance.reality.reality_contamination_guard import RealityContaminationGuard
from governance.reality.truth_override_detector import TruthOverrideDetector


@dataclass
class RealityIntegrityVerdict:
    integrity_ok: bool
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "integrity_ok": self.integrity_ok,
            "issues": list(self.issues),
        }


class RealityIntegrityMonitor:
    def __init__(self) -> None:
        self._alignment = RealityAlignment()
        self._contamination = RealityContaminationGuard()
        self._override = TruthOverrideDetector()

    def check(self, text: str) -> RealityIntegrityVerdict:
        align = self._alignment.evaluate(text)
        contam = self._contamination.scan(text)
        override = self._override.scan(text)
        issues = list(align.reasons)
        if contam.contaminated:
            issues.extend(contam.signals)
        if override.override_detected:
            issues.extend(override.signals)
        return RealityIntegrityVerdict(
            integrity_ok=align.aligned and not contam.contaminated and not override.override_detected,
            issues=issues,
        )
