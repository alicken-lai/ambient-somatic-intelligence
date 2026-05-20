"""Contradiction detector — conflicting salience/confidence clusters."""

from __future__ import annotations

from governance.identity.provenance_record import ProvenanceRecord
from observability.v04.metric_normalizer import clamp01


class ContradictionDetector:
    """Advisory contradiction pressure; never claims deterministic truth."""

    CONFLICT_CONFIDENCE_GAP = 0.45

    def pressure(self, recent: list[ProvenanceRecord]) -> float:
        if len(recent) < 2:
            return 0.0
        confs = [r.confidence for r in recent if not r.corrupted]
        if len(confs) < 2:
            return 0.0
        spread = max(confs) - min(confs)
        domains = {r.target_key.split(":")[0] for r in recent if r.target_key}
        domain_penalty = 0.15 if len(domains) > 3 else 0.0
        gap_penalty = 0.25 if spread > self.CONFLICT_CONFIDENCE_GAP else 0.0
        return clamp01(gap_penalty + domain_penalty)

    def has_contradiction(self, recent: list[ProvenanceRecord]) -> bool:
        return self.pressure(recent) >= 0.35
