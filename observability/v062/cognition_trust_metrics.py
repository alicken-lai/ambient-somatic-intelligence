"""Cognition trust realism metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.identity.cognitive_identity import CognitiveIdentity
from governance.identity.provenance_record import ProvenanceRecord
from governance.identity.trusted_cognition import is_trusted_cognition


@dataclass
class CognitionTrustMetrics:
    trust_rate: float = 1.0
    mean_authority_multiplier: float = 1.0
    uncertain_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "trust_rate": round(self.trust_rate, 4),
            "mean_authority_multiplier": round(self.mean_authority_multiplier, 4),
            "uncertain_rate": round(self.uncertain_rate, 4),
        }


def collect_cognition_trust_metrics(
    records: list[ProvenanceRecord] | None = None,
) -> CognitionTrustMetrics:
    identity = CognitiveIdentity()
    if records is None:
        records = []
        for conf, meta in [(0.85, {}), (0.4, {"provenance_uncertain": True}), (0.8, {"memory_activation": True})]:
            r = identity.build_record_from_target(
                source_domain="telemetry",
                signal_type="t",
                route_name="attention_submit",
                raw_confidence=conf,
                metadata=meta,
            )
            identity.register(r)
            records.append(r)
    from governance.identity.trusted_cognition import trusted_authority_multiplier
    from governance.identity.uncertain_cognition import uncertain_authority_multiplier

    n = len(records) or 1
    trusted = sum(1 for r in records if is_trusted_cognition(r))
    mults = []
    for r in records:
        if is_trusted_cognition(r):
            mults.append(trusted_authority_multiplier(r))
        else:
            mults.append(uncertain_authority_multiplier(r))
    return CognitionTrustMetrics(
        trust_rate=trusted / n,
        mean_authority_multiplier=sum(mults) / len(mults) if mults else 1.0,
        uncertain_rate=1.0 - trusted / n,
    )
