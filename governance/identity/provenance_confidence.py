"""Provenance confidence scoring."""

from __future__ import annotations

from governance.identity.cognition_origin import CognitionOrigin
from governance.identity.provenance_record import ProvenanceRecord
from observability.v04.metric_normalizer import clamp01


def score_provenance_confidence(record: ProvenanceRecord) -> float:
    if record.corrupted:
        return 0.0
    base = record.provenance_confidence
    if record.origin == CognitionOrigin.FOREIGN:
        base *= 0.6
    if record.origin == CognitionOrigin.UNCERTAIN:
        base *= 0.75
    return clamp01(base)
