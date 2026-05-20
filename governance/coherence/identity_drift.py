"""Identity drift — bounded signature drift across recent cognition."""

from __future__ import annotations

from governance.identity.provenance_record import ProvenanceRecord
from observability.v04.metric_normalizer import clamp01


class IdentityDrift:
    MAX_UNIQUE_SIGNATURES = 12
    DRIFT_WINDOW = 20

    def pressure(self, recent: list[ProvenanceRecord]) -> float:
        window = recent[-self.DRIFT_WINDOW :]
        if len(window) < 3:
            return 0.0
        unique = len({r.identity_signature for r in window})
        if unique <= self.MAX_UNIQUE_SIGNATURES:
            return 0.0
        excess = unique - self.MAX_UNIQUE_SIGNATURES
        return clamp01(excess * 0.08)

    def drift_bounded(self, recent: list[ProvenanceRecord]) -> bool:
        return self.pressure(recent) < 0.45
