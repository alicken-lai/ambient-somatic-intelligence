"""Uncertain cognition — damp authority when provenance is weak."""

from __future__ import annotations

from governance.identity.cognition_origin import CognitionOrigin
from governance.identity.provenance_record import ProvenanceRecord
from governance.identity.trusted_cognition import is_trusted_cognition
from observability.v04.metric_normalizer import clamp01

UNCERTAIN_DAMP_FLOOR = 0.35


def is_uncertain_cognition(record: ProvenanceRecord) -> bool:
    if record.corrupted:
        return True
    return record.origin in {
        CognitionOrigin.UNCERTAIN,
        CognitionOrigin.FOREIGN,
    } or record.provenance_confidence < 0.5


def uncertain_authority_multiplier(record: ProvenanceRecord) -> float:
    if is_trusted_cognition(record):
        return 1.0
    if record.corrupted:
        return 0.0
    if is_uncertain_cognition(record):
        conf = clamp01(record.provenance_confidence)
        return clamp01(max(UNCERTAIN_DAMP_FLOOR, conf * 0.85))
    if record.origin == CognitionOrigin.SYNTHETIC:
        return 0.55
    if record.origin.is_replay_derived:
        return clamp01(0.65 + record.provenance_confidence * 0.2)
    return 1.0


def damp_salience(base_salience: float, record: ProvenanceRecord) -> float:
    return clamp01(base_salience * uncertain_authority_multiplier(record))
