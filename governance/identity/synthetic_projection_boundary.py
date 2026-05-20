"""Synthetic projection boundary — contain forecast/synthetic cognition."""

from __future__ import annotations

from governance.identity.cognition_origin import CognitionOrigin
from governance.identity.provenance_record import ProvenanceRecord
from observability.v04.metric_normalizer import clamp01

SYNTHETIC_SALIENCE_CEILING = 0.65


class SyntheticProjectionBoundary:
    def contain(self, record: ProvenanceRecord) -> bool:
        if record.origin != CognitionOrigin.SYNTHETIC:
            return True
        meta = record.metadata
        if meta.get("unbounded_synthetic"):
            return False
        if record.confidence > 0.92 and not meta.get("synthetic_labeled"):
            return False
        return True

    def bounded_salience(self, salience: float, record: ProvenanceRecord) -> float:
        if record.origin != CognitionOrigin.SYNTHETIC:
            return salience
        return clamp01(min(salience, SYNTHETIC_SALIENCE_CEILING))
