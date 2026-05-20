"""Provenance integrity metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.identity.cognitive_identity import CognitiveIdentity
from governance.identity.provenance_record import ProvenanceRecord
from governance.identity.cognition_origin import CognitionOrigin


@dataclass
class ProvenanceMetrics:
    integrity_rate: float = 1.0
    labeled_rate: float = 1.0
    corruption_detected: int = 0
    sample_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "integrity_rate": round(self.integrity_rate, 4),
            "labeled_rate": round(self.labeled_rate, 4),
            "corruption_detected": self.corruption_detected,
            "sample_count": self.sample_count,
        }


def collect_provenance_metrics(
    records: list[ProvenanceRecord] | None = None,
) -> ProvenanceMetrics:
    if records is None:
        identity = CognitiveIdentity()
        records = []
        samples = [
            ("telemetry", "live", 0.8, 0.0, {}),
            ("memory", "recall", 0.75, 0.0, {"memory_activation": True}),
            ("telemetry", "replay", 0.7, 0.6, {"replay_derived": True, "replay_labeled": True}),
            ("forecast", "proj", 0.65, 0.0, {"synthetic_projection": True, "synthetic_labeled": True}),
        ]
        for domain, sig, conf, rh, meta in samples:
            r = identity.build_record_from_target(
                source_domain=domain,
                signal_type=sig,
                route_name="attention_submit",
                raw_confidence=conf,
                replay_hint=rh,
                metadata=meta,
            )
            identity.register(r)
            records.append(r)
    n = len(records) or 1
    corrupted = sum(1 for r in records if r.corrupted)
    labeled = sum(1 for r in records if r.origin != CognitionOrigin.UNCERTAIN)
    integrity = (n - corrupted) / n
    return ProvenanceMetrics(
        integrity_rate=integrity,
        labeled_rate=labeled / n,
        corruption_detected=corrupted,
        sample_count=n,
    )
