"""Cognitive identity — bounded continuity and provenance registry."""

from __future__ import annotations

from typing import Any

from governance.identity.cognition_lineage import CognitionLineage
from governance.identity.cognition_origin import CognitionOrigin
from governance.identity.continuity_anchor import ContinuityAnchor
from governance.identity.fragmentation_guard import FragmentationGuard
from governance.identity.identity_coherence import IdentityCoherence
from governance.identity.identity_decision import IdentityDecision
from governance.identity.identity_decay import IdentityDecay
from governance.identity.memory_provenance_guard import MemoryProvenanceGuard
from governance.identity.provenance_record import ProvenanceRecord
from governance.identity.replay_identity_boundary import ReplayIdentityBoundary
from governance.identity.runtime_identity import RuntimeIdentity
from governance.identity.synthetic_projection_boundary import SyntheticProjectionBoundary
from governance.identity.trusted_cognition import (
    is_trusted_cognition,
    trusted_authority_multiplier,
)
from governance.identity.uncertain_cognition import uncertain_authority_multiplier
from observability.v04.metric_normalizer import clamp01


class CognitiveIdentity:
    """
    Tracks cognition provenance and applies bounded identity decisions.

    Advisory only — does not execute side effects or claim consciousness.
    """

    def __init__(self) -> None:
        self.runtime = RuntimeIdentity()
        self.lineage = CognitionLineage()
        self.coherence = IdentityCoherence()
        self.fragmentation = FragmentationGuard()
        self.decay = IdentityDecay()
        self.replay_boundary = ReplayIdentityBoundary()
        self.memory_guard = MemoryProvenanceGuard()
        self.synthetic_boundary = SyntheticProjectionBoundary()
        self._registry: list[ProvenanceRecord] = []

    def register(
        self,
        record: ProvenanceRecord,
        *,
        session_id: str = "default",
    ) -> IdentityDecision:
        self._registry.append(record)
        self.lineage.append(record)
        anchor = self.runtime.anchor_for(session_id, record.identity_signature)
        trace = ["cognitive_identity_register", f"origin:{record.origin.value}"]

        replay_sep = self.replay_boundary.separate_replay(record)
        if not replay_sep:
            trace.append("replay_impersonation_blocked")

        synth_ok = self.synthetic_boundary.contain(record)
        if not synth_ok:
            trace.append("synthetic_bounded")

        mem_ok = self.memory_guard.label_memory_origin(record)
        if not mem_ok:
            trace.append("memory_provenance_rejected")

        coherent = self.coherence.check(self._registry[-20:])
        frag_ok = self.fragmentation.check_signatures(
            [r.identity_signature for r in self._registry[-30:]]
        )
        decay_mult = self.decay.multiplier(len(self._registry))

        if record.corrupted:
            return IdentityDecision(
                trusted=False,
                authority_multiplier=0.0,
                provenance=record,
                reason="provenance_corrupted",
                replay_separated=replay_sep,
                synthetic_bounded=synth_ok,
                coherence_ok=False,
                trace=trace + ["corruption_detected"],
            )

        if not replay_sep:
            return IdentityDecision(
                trusted=False,
                authority_multiplier=0.0,
                provenance=record,
                reason="replay_impersonation",
                replay_separated=False,
                synthetic_bounded=synth_ok,
                coherence_ok=coherent,
                trace=trace,
            )

        if not synth_ok or not mem_ok:
            mult = clamp01(0.4 * decay_mult)
            return IdentityDecision(
                trusted=False,
                authority_multiplier=mult,
                provenance=record,
                reason="boundary_violation",
                replay_separated=replay_sep,
                synthetic_bounded=synth_ok,
                coherence_ok=coherent,
                trace=trace,
            )

        if not coherent or not frag_ok:
            mult = clamp01(uncertain_authority_multiplier(record) * 0.7 * decay_mult)
            return IdentityDecision(
                trusted=False,
                authority_multiplier=mult,
                provenance=record,
                reason="identity_fragmentation",
                replay_separated=replay_sep,
                synthetic_bounded=synth_ok,
                coherence_ok=False,
                trace=trace + ["fragmentation_damped"],
            )

        trusted = is_trusted_cognition(record)
        if trusted:
            mult = clamp01(trusted_authority_multiplier(record) * decay_mult)
        else:
            mult = clamp01(uncertain_authority_multiplier(record) * decay_mult)

        anchor.verify_chain(self.lineage.chain_tail(5))
        reason = "trusted_runtime" if trusted else "provenance_damped"
        if record.origin == CognitionOrigin.REPLAY:
            reason = "replay_bounded"

        return IdentityDecision(
            trusted=trusted,
            authority_multiplier=mult,
            provenance=record,
            reason=reason,
            replay_separated=replay_sep,
            synthetic_bounded=synth_ok,
            coherence_ok=coherent,
            trace=trace + [f"anchor:{anchor.anchor_id[:8]}"],
        )

    def build_record_from_target(
        self,
        *,
        source_domain: str,
        signal_type: str,
        route_name: str,
        raw_confidence: float,
        replay_hint: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> ProvenanceRecord:
        return ProvenanceRecord.from_target(
            source_domain=source_domain,
            signal_type=signal_type,
            route_name=route_name,
            raw_confidence=raw_confidence,
            replay_hint=replay_hint,
            metadata=metadata,
        )

    @property
    def registry_size(self) -> int:
        return len(self._registry)
