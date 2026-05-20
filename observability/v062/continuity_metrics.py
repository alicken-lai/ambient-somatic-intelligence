"""Continuity stability metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.identity.cognition_lineage import CognitionLineage
from governance.identity.cognitive_identity import CognitiveIdentity
from governance.identity.runtime_identity import RuntimeIdentity


@dataclass
class ContinuityMetrics:
    anchor_stability_rate: float = 1.0
    lineage_verified: bool = True
    anchor_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "anchor_stability_rate": round(self.anchor_stability_rate, 4),
            "lineage_verified": self.lineage_verified,
            "anchor_count": self.anchor_count,
        }


def collect_continuity_metrics() -> ContinuityMetrics:
    identity = CognitiveIdentity()
    runtime = RuntimeIdentity(session_id="gate-session")
    lineage = CognitionLineage()
    for i in range(5):
        r = identity.build_record_from_target(
            source_domain="telemetry",
            signal_type=f"c{i}",
            route_name="attention_submit",
            raw_confidence=0.8,
        )
        identity.register(r)
        runtime.anchor_for("gate-session", r.identity_signature)
        lineage.append(r)
    verified = sum(1 for a in runtime.anchors.values() if a.chain_verified)
    n = len(runtime.anchors) or 1
    return ContinuityMetrics(
        anchor_stability_rate=verified / n,
        lineage_verified=lineage.verify_chain(),
        anchor_count=len(runtime.anchors),
    )
