"""Fragmentation pressure — sprawl of origins and signatures."""

from __future__ import annotations

from governance.identity.fragmentation_guard import FragmentationGuard
from governance.identity.provenance_record import ProvenanceRecord
from observability.v04.metric_normalizer import clamp01


class FragmentationPressure:
    def __init__(self) -> None:
        self.guard = FragmentationGuard()

    def pressure(self, recent: list[ProvenanceRecord]) -> float:
        if not recent:
            return 0.0
        sigs = [r.identity_signature for r in recent]
        if not self.guard.check_signatures(sigs):
            return 0.85
        origins = {r.origin for r in recent if not r.corrupted}
        origin_penalty = 0.2 if len(origins) > 4 else 0.0
        return clamp01(origin_penalty)
