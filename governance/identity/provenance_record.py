"""Provenance record — required metadata for cognition pathways."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from governance.identity.cognition_origin import CognitionOrigin
from governance.identity.identity_signature import compute_identity_signature
from observability.v04.metric_normalizer import clamp01


@dataclass
class ProvenanceRecord:
    origin: CognitionOrigin
    route_name: str
    confidence: float
    provenance_confidence: float
    identity_signature: str
    target_key: str = ""
    registered_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)
    corrupted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "origin": self.origin.value,
            "route_name": self.route_name,
            "confidence": round(self.confidence, 4),
            "provenance_confidence": round(self.provenance_confidence, 4),
            "identity_signature": self.identity_signature,
            "target_key": self.target_key,
            "registered_at": self.registered_at,
            "corrupted": self.corrupted,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_target(
        cls,
        *,
        source_domain: str,
        signal_type: str,
        route_name: str,
        raw_confidence: float,
        replay_hint: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> ProvenanceRecord:
        meta = dict(metadata or {})
        origin = cls._infer_origin(
            source_domain=source_domain,
            replay_hint=replay_hint,
            metadata=meta,
        )
        prov_conf = cls._provenance_confidence(origin, meta, replay_hint)
        target_key = f"{source_domain}:{signal_type}"
        sig = compute_identity_signature(
            origin=origin,
            route_name=route_name,
            target_key=target_key,
            metadata=meta,
        )
        corrupted = bool(meta.get("provenance_corrupted")) or prov_conf < 0.15
        return cls(
            origin=origin,
            route_name=route_name,
            confidence=clamp01(raw_confidence),
            provenance_confidence=prov_conf,
            identity_signature=sig,
            target_key=target_key,
            metadata=meta,
            corrupted=corrupted,
        )

    @staticmethod
    def _infer_origin(
        *,
        source_domain: str,
        replay_hint: float,
        metadata: dict[str, Any],
    ) -> CognitionOrigin:
        if metadata.get("synthetic_projection"):
            return CognitionOrigin.SYNTHETIC
        if metadata.get("foreign_cognition"):
            return CognitionOrigin.FOREIGN
        if replay_hint > 0.55 or metadata.get("replay_derived"):
            return CognitionOrigin.REPLAY
        if metadata.get("inherited_context"):
            return CognitionOrigin.INHERITED
        if metadata.get("memory_activation") or source_domain == "memory":
            return CognitionOrigin.MEMORY
        if metadata.get("provenance_uncertain") or metadata.get("ambiguous_owner"):
            return CognitionOrigin.UNCERTAIN
        return CognitionOrigin.RUNTIME

    @staticmethod
    def _provenance_confidence(
        origin: CognitionOrigin,
        metadata: dict[str, Any],
        replay_hint: float,
    ) -> float:
        base = {
            CognitionOrigin.RUNTIME: 0.92,
            CognitionOrigin.MEMORY: 0.85,
            CognitionOrigin.REPLAY: 0.72,
            CognitionOrigin.INHERITED: 0.68,
            CognitionOrigin.SYNTHETIC: 0.55,
            CognitionOrigin.FOREIGN: 0.35,
            CognitionOrigin.UNCERTAIN: 0.4,
        }[origin]
        if metadata.get("provenance_corrupted"):
            return 0.05
        if replay_hint > 0.7:
            base *= 0.85
        explicit = metadata.get("provenance_confidence")
        if isinstance(explicit, (int, float)):
            return clamp01(float(explicit))
        return clamp01(base)
