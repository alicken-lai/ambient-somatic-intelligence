"""Reality alignment — coordinate operational truth without sovereign merge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.reality.bounded_consensus import BoundedConsensus
from governance.reality.divergence_detector import DivergenceDetector
from governance.reality.reality_boundary import RealityBoundary
from governance.reality.reality_contamination_guard import RealityContaminationGuard
from governance.reality.truth_override_detector import TruthOverrideDetector


@dataclass
class RealityAlignmentVerdict:
    aligned: bool
    advisory_only: bool = True
    divergence_bounded: bool = True
    contamination_free: bool = True
    override_free: bool = True
    bounded_consensus_ok: bool = True
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "aligned": self.aligned,
            "advisory_only": self.advisory_only,
            "divergence_bounded": self.divergence_bounded,
            "contamination_free": self.contamination_free,
            "override_free": self.override_free,
            "bounded_consensus_ok": self.bounded_consensus_ok,
            "reasons": list(self.reasons),
        }


class RealityAlignment:
    """
    Evaluates cross-runtime reality alignment proposals.

    Never merges sovereign realities or overrides Guardian/constitution.
    """

    def __init__(self) -> None:
        self._boundary = RealityBoundary()
        self._divergence = DivergenceDetector()
        self._contamination = RealityContaminationGuard()
        self._override = TruthOverrideDetector()
        self._consensus = BoundedConsensus()

    def evaluate(
        self,
        text: str,
        *,
        left_runtime: str = "ambient",
        right_runtime: str = "foreign",
        scope: str = "advisory",
    ) -> RealityAlignmentVerdict:
        reasons: list[str] = []
        boundary = self._boundary.evaluate(text, scope=scope)
        if not boundary.boundary_safe:
            reasons.extend(boundary.violations)

        div = self._divergence.detect(text, left_runtime=left_runtime, right_runtime=right_runtime)
        if not div.bounded:
            reasons.extend(div.signals)

        contam = self._contamination.scan(text)
        if contam.contaminated:
            reasons.extend(contam.signals)

        override = self._override.scan(text)
        if override.override_detected:
            reasons.extend(override.signals)

        consensus = self._consensus.evaluate(text)
        if not consensus.bounded:
            reasons.append("unbounded_consensus_pressure")

        aligned = (
            boundary.boundary_safe
            and div.bounded
            and not contam.contaminated
            and not override.override_detected
            and consensus.bounded
        )
        return RealityAlignmentVerdict(
            aligned=aligned,
            divergence_bounded=div.bounded,
            contamination_free=not contam.contaminated,
            override_free=not override.override_detected,
            bounded_consensus_ok=consensus.bounded,
            reasons=reasons,
        )
