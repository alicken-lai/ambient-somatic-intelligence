"""Identity coherence — detect conflicting provenance clusters."""

from __future__ import annotations

from governance.identity.cognition_origin import CognitionOrigin
from governance.identity.provenance_record import ProvenanceRecord


class IdentityCoherence:
    MAX_DISTINCT_ORIGINS = 4

    def check(self, recent: list[ProvenanceRecord]) -> bool:
        if len(recent) < 3:
            return True
        origins = {r.origin for r in recent if not r.corrupted}
        if len(origins) > self.MAX_DISTINCT_ORIGINS:
            return False
        live = sum(1 for r in recent if r.origin == CognitionOrigin.RUNTIME)
        replay = sum(1 for r in recent if r.origin == CognitionOrigin.REPLAY)
        if replay > live * 2 and live > 0:
            return False
        return True
