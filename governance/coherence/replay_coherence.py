"""Replay coherence — replay must not dominate live cognition narrative."""

from __future__ import annotations

from governance.identity.cognition_origin import CognitionOrigin
from governance.identity.provenance_record import ProvenanceRecord
from observability.v04.metric_normalizer import clamp01


class ReplayCoherence:
    MAX_REPLAY_SHARE = 0.55

    def pressure(self, recent: list[ProvenanceRecord]) -> float:
        if not recent:
            return 0.0
        live = sum(1 for r in recent if r.origin == CognitionOrigin.RUNTIME)
        replay = sum(1 for r in recent if r.origin == CognitionOrigin.REPLAY)
        total = live + replay
        if total == 0:
            return 0.0
        share = replay / total
        if share <= self.MAX_REPLAY_SHARE:
            return 0.0
        return clamp01((share - self.MAX_REPLAY_SHARE) * 2.0)

    def coherent(self, recent: list[ProvenanceRecord]) -> bool:
        return self.pressure(recent) < 0.4
