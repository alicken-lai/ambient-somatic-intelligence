"""Identity stability composite (pre-gate rollup)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from observability.v04.metric_normalizer import clamp01
from observability.v062.cognition_trust_metrics import collect_cognition_trust_metrics
from observability.v062.continuity_metrics import collect_continuity_metrics
from observability.v062.fragmentation_metrics import collect_fragmentation_metrics
from observability.v062.identity_coherence_metrics import collect_identity_coherence_metrics
from observability.v062.provenance_metrics import collect_provenance_metrics


@dataclass
class IdentityStabilitySnapshot:
    composite: float = 0.0
    provenance_integrity: float = 1.0
    trust_realism: float = 1.0
    coherence: float = 1.0
    fragmentation_resistance: float = 1.0
    continuity: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "composite": round(self.composite, 4),
            "provenance_integrity": round(self.provenance_integrity, 4),
            "trust_realism": round(self.trust_realism, 4),
            "coherence": round(self.coherence, 4),
            "fragmentation_resistance": round(self.fragmentation_resistance, 4),
            "continuity": round(self.continuity, 4),
        }


def collect_identity_stability_snapshot() -> IdentityStabilitySnapshot:
    prov = collect_provenance_metrics()
    trust = collect_cognition_trust_metrics()
    coh = collect_identity_coherence_metrics()
    frag = collect_fragmentation_metrics()
    cont = collect_continuity_metrics()
    dims = [
        prov.integrity_rate,
        trust.trust_rate,
        coh.coherence_rate,
        frag.resistance_rate,
        cont.anchor_stability_rate,
    ]
    composite = clamp01(sum(dims) / len(dims))
    return IdentityStabilitySnapshot(
        composite=composite,
        provenance_integrity=prov.integrity_rate,
        trust_realism=trust.trust_rate,
        coherence=coh.coherence_rate,
        fragmentation_resistance=frag.resistance_rate,
        continuity=cont.anchor_stability_rate,
    )
