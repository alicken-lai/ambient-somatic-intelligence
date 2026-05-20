"""Cognitive coherence — evaluate cross-layer consistency after governance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.coherence.coherence_decay import CoherenceDecay
from governance.coherence.constitutional_coherence import ConstitutionalCoherence
from governance.coherence.contradiction_detector import ContradictionDetector
from governance.coherence.fragmentation_pressure import FragmentationPressure
from governance.coherence.identity_drift import IdentityDrift
from governance.coherence.replay_coherence import ReplayCoherence
from governance.identity.provenance_record import ProvenanceRecord
from observability.v04.metric_normalizer import clamp01


@dataclass
class CoherenceVerdict:
    coherent: bool
    score: float
    contradiction_pressure: float = 0.0
    replay_pressure: float = 0.0
    constitutional_pressure: float = 0.0
    drift_pressure: float = 0.0
    fragmentation_pressure: float = 0.0
    reasons: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "coherent": self.coherent,
            "score": round(self.score, 4),
            "contradiction_pressure": round(self.contradiction_pressure, 4),
            "replay_pressure": round(self.replay_pressure, 4),
            "constitutional_pressure": round(self.constitutional_pressure, 4),
            "drift_pressure": round(self.drift_pressure, 4),
            "fragmentation_pressure": round(self.fragmentation_pressure, 4),
            "reasons": list(self.reasons),
            "trace": list(self.trace),
            "disclaimer": "coherence_advisory_not_consciousness_claim",
        }


class CognitiveCoherence:
    """
    Bounded coherence evaluation after governance, before final output.

    Preserves probabilistic cognition; does not claim consciousness.
    """

    COHERENCE_FLOOR = 0.55

    def __init__(self) -> None:
        self.contradictions = ContradictionDetector()
        self.replay = ReplayCoherence()
        self.constitutional = ConstitutionalCoherence()
        self.drift = IdentityDrift()
        self.fragmentation = FragmentationPressure()
        self.decay = CoherenceDecay()
        self._evaluations = 0
        self._recent: list[ProvenanceRecord] = []

    def ingest_record(self, record: ProvenanceRecord) -> None:
        self._recent.append(record)
        if len(self._recent) > 40:
            self._recent = self._recent[-40:]

    def evaluate_after_governance(
        self,
        *,
        governed_salience: float,
        constitutional_compliant: bool = True,
        constitutional_verdict: dict[str, Any] | None = None,
        identity_trusted: bool = True,
        provenance: dict[str, Any] | None = None,
        recent: list[ProvenanceRecord] | None = None,
    ) -> CoherenceVerdict:
        self._evaluations += 1
        window = list(recent if recent is not None else self._recent)
        _ = provenance  # reserved for explainability payloads

        contra_p = self.contradictions.pressure(window)
        replay_p = self.replay.pressure(window)
        const_p = self.constitutional.pressure(
            constitutional_compliant=constitutional_compliant,
            constitutional_verdict=constitutional_verdict,
        )
        drift_p = self.drift.pressure(window)
        frag_p = self.fragmentation.pressure(window)

        composite_pressure = clamp01(
            contra_p * 0.28
            + replay_p * 0.22
            + const_p * 0.25
            + drift_p * 0.15
            + frag_p * 0.10
        )
        decay_mult = self.decay.multiplier(self._evaluations)
        base = clamp01(1.0 - composite_pressure) * decay_mult
        if governed_salience < 0.05:
            base = clamp01(base * 0.95)
        if not identity_trusted:
            base = clamp01(base * 0.85)

        reasons: list[str] = []
        if contra_p >= 0.35:
            reasons.append("contradiction_pressure")
        if replay_p >= 0.4:
            reasons.append("replay_dominance")
        if const_p >= 0.35:
            reasons.append("constitutional_misalignment")
        if drift_p >= 0.45:
            reasons.append("identity_drift")
        if frag_p >= 0.35:
            reasons.append("fragmentation_pressure")

        coherent = base >= self.COHERENCE_FLOOR and len(reasons) == 0
        trace = [
            "cognitive_coherence_evaluate",
            f"pressure:{composite_pressure:.3f}",
            f"score:{base:.3f}",
        ]

        return CoherenceVerdict(
            coherent=coherent,
            score=base,
            contradiction_pressure=contra_p,
            replay_pressure=replay_p,
            constitutional_pressure=const_p,
            drift_pressure=drift_p,
            fragmentation_pressure=frag_p,
            reasons=reasons,
            trace=trace,
        )

    def damp_salience(self, salience: float, verdict: CoherenceVerdict) -> float:
        if verdict.coherent:
            return salience
        return clamp01(salience * max(0.5, verdict.score))
