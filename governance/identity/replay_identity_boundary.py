"""Replay identity boundary — replay cannot impersonate live runtime cognition."""

from __future__ import annotations

from governance.identity.cognition_origin import CognitionOrigin
from governance.identity.provenance_record import ProvenanceRecord


class ReplayIdentityBoundary:
    """Separates replay-derived cognition from live runtime pathways."""

    IMPERSONATION_REPLAY_HINT = 0.85

    def separate_replay(self, record: ProvenanceRecord) -> bool:
        meta = record.metadata
        if record.origin != CognitionOrigin.REPLAY:
            return True
        if meta.get("impersonate_runtime"):
            return False
        if meta.get("replay_as_live"):
            return False
        if record.route_name == "attention_submit" and record.confidence > 0.95:
            if meta.get("replay_derived") and not meta.get("replay_labeled"):
                return False
        return True

    def is_replay_derived(self, record: ProvenanceRecord) -> bool:
        return record.origin.is_replay_derived
