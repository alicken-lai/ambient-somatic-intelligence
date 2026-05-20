"""Trusted cognition — high-provenance authority preservation."""

from __future__ import annotations

from governance.identity.cognition_origin import CognitionOrigin
from governance.identity.provenance_confidence import score_provenance_confidence
from governance.identity.provenance_record import ProvenanceRecord
from observability.v04.metric_normalizer import clamp01

TRUST_THRESHOLD = 0.72


def is_trusted_cognition(record: ProvenanceRecord) -> bool:
    if record.corrupted:
        return False
    if record.origin in {CognitionOrigin.FOREIGN, CognitionOrigin.UNCERTAIN}:
        return False
    return score_provenance_confidence(record) >= TRUST_THRESHOLD


def trusted_authority_multiplier(record: ProvenanceRecord) -> float:
    if not is_trusted_cognition(record):
        return 1.0
    conf = score_provenance_confidence(record)
    return clamp01(0.92 + (conf - TRUST_THRESHOLD) * 0.15)
