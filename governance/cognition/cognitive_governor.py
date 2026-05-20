"""Cognitive governor — advisory arbitration over attention salience."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.calibration.confidence_cap import apply_confidence_cap
from attention.core.attention_target import AttentionTarget
from governance.cognition.arbitration_engine import ArbitrationEngine, ArbitrationResult
from governance.cognition.salience_arbitrator import SalienceClaim
from governance.cognition.sovereignty_limits import SovereigntyLimitsChecker
from governance.constitution.constitutional_guard import ConstitutionalContext, ConstitutionalGuard
from governance.coherence.cognitive_coherence import CognitiveCoherence, CoherenceVerdict
from governance.homeostasis.cognitive_homeostasis import HomeostasisVerdict
from governance.metacognition.metacognitive_reflection import (
    MetacognitiveReflection,
    MetacognitiveVerdict,
)
from governance.identity.cognitive_identity import CognitiveIdentity
from governance.identity.identity_decision import IdentityDecision
from governance.identity.provenance_record import ProvenanceRecord
from governance.identity.synthetic_projection_boundary import SyntheticProjectionBoundary
from governance.identity.uncertain_cognition import damp_salience
from governance.civilization.civilization_observability import observe_civilization
from governance.reality.reality_alignment_observability import observe_reality_alignment
from governance.temporal.temporal_continuity_observability import observe_temporal_continuity
from governance.meaning.semantic_continuity_observability import observe_semantic_continuity
from governance.value.value_continuity_observability import observe_value_continuity
from governance.intent.intent_continuity_observability import observe_intent_continuity
from governance.purpose.purpose_boundary_observability import observe_purpose_boundary
from governance.agency.agency_boundary_observability import observe_agency_boundary
from governance.external.runtime.runtime_external_observability import observe_runtime_external
from hermes.skills.external.external_skill_registry import ExternalSkillRegistry
from observability.v04.metric_normalizer import clamp01


@dataclass
class GovernanceDecision:
    """Advisory outcome — does not execute side effects."""

    accepted: bool
    governed_salience: float
    arbitration: ArbitrationResult
    reason: str = "ok"
    autonomous_blocked: bool = False
    constitutional_compliant: bool = True
    constitutional_blocked: bool = False
    constitutional_verdict: dict[str, Any] | None = None
    provenance: dict[str, Any] | None = None
    identity_trusted: bool = True
    identity_authority_multiplier: float = 1.0
    coherence_ok: bool = True
    coherence_score: float = 1.0
    coherence_verdict: dict[str, Any] | None = None
    metacognitive_reflective: bool = True
    metacognition_score: float = 1.0
    metacognitive_verdict: dict[str, Any] | None = None
    homeostasis_stable: bool = True
    homeostasis_score: float = 1.0
    homeostasis_verdict: dict[str, Any] | None = None
    stabilization_recommendations: list[str] = field(default_factory=list)
    external_advisory: dict[str, Any] | None = None
    runtime_external_observability: dict[str, Any] | None = None
    civilization_observability: dict[str, Any] | None = None
    reality_alignment_observability: dict[str, Any] | None = None
    temporal_continuity_observability: dict[str, Any] | None = None
    semantic_continuity_observability: dict[str, Any] | None = None
    value_continuity_observability: dict[str, Any] | None = None
    intent_continuity_observability: dict[str, Any] | None = None
    purpose_boundary_observability: dict[str, Any] | None = None
    agency_boundary_observability: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "accepted": self.accepted,
            "governed_salience": round(self.governed_salience, 4),
            "reason": self.reason,
            "autonomous_blocked": self.autonomous_blocked,
            "constitutional_compliant": self.constitutional_compliant,
            "constitutional_blocked": self.constitutional_blocked,
            "arbitration": self.arbitration.to_dict(),
        }
        if self.constitutional_verdict is not None:
            out["constitutional_verdict"] = self.constitutional_verdict
        if self.provenance is not None:
            out["provenance"] = self.provenance
        out["identity_trusted"] = self.identity_trusted
        out["identity_authority_multiplier"] = round(self.identity_authority_multiplier, 4)
        out["coherence_ok"] = self.coherence_ok
        out["coherence_score"] = round(self.coherence_score, 4)
        if self.coherence_verdict is not None:
            out["coherence_verdict"] = self.coherence_verdict
        out["metacognitive_reflective"] = self.metacognitive_reflective
        out["metacognition_score"] = round(self.metacognition_score, 4)
        if self.metacognitive_verdict is not None:
            out["metacognitive_verdict"] = self.metacognitive_verdict
        out["homeostasis_stable"] = self.homeostasis_stable
        out["homeostasis_score"] = round(self.homeostasis_score, 4)
        if self.homeostasis_verdict is not None:
            out["homeostasis_verdict"] = self.homeostasis_verdict
        if self.stabilization_recommendations:
            out["stabilization_recommendations"] = list(self.stabilization_recommendations)
        if self.external_advisory is not None:
            out["external_advisory"] = dict(self.external_advisory)
        if self.runtime_external_observability is not None:
            out["runtime_external_observability"] = dict(
                self.runtime_external_observability
            )
        if self.civilization_observability is not None:
            out["civilization_observability"] = dict(self.civilization_observability)
        if self.reality_alignment_observability is not None:
            out["reality_alignment_observability"] = dict(
                self.reality_alignment_observability
            )
        if self.temporal_continuity_observability is not None:
            out["temporal_continuity_observability"] = dict(
                self.temporal_continuity_observability
            )
        if self.semantic_continuity_observability is not None:
            out["semantic_continuity_observability"] = dict(
                self.semantic_continuity_observability
            )
        if self.value_continuity_observability is not None:
            out["value_continuity_observability"] = dict(
                self.value_continuity_observability
            )
        if self.intent_continuity_observability is not None:
            out["intent_continuity_observability"] = dict(
                self.intent_continuity_observability
            )
        if self.purpose_boundary_observability is not None:
            out["purpose_boundary_observability"] = dict(
                self.purpose_boundary_observability
            )
        if self.agency_boundary_observability is not None:
            out["agency_boundary_observability"] = dict(
                self.agency_boundary_observability
            )
        return out


class CognitiveGovernor:
    """
    Governs salience proposals before kernel submit.

    Preserves probabilistic cognition; never claims deterministic authority.
    """

    def __init__(self) -> None:
        self.engine = ArbitrationEngine(governance_depth=1)
        self.sovereignty = SovereigntyLimitsChecker()
        self.constitutional_guard = ConstitutionalGuard()
        self.cognitive_identity = CognitiveIdentity()
        self.synthetic_boundary = SyntheticProjectionBoundary()
        self.cognitive_coherence = CognitiveCoherence()
        self.metacognitive_reflection = MetacognitiveReflection()
        self.external_skills = ExternalSkillRegistry()

    def _attach_runtime_observability(
        self,
        decision: GovernanceDecision,
        *,
        route_name: str,
    ) -> GovernanceDecision:
        """Runtime soak observability — never overrides acceptance or salience."""
        hints = decision.external_advisory or {}
        payload = " ".join(str(h) for h in hints.get("hints", [])) or route_name
        obs = observe_runtime_external(payload, scope="advisory")
        return GovernanceDecision(
            accepted=decision.accepted,
            governed_salience=decision.governed_salience,
            arbitration=decision.arbitration,
            reason=decision.reason,
            autonomous_blocked=decision.autonomous_blocked,
            constitutional_compliant=decision.constitutional_compliant,
            constitutional_blocked=decision.constitutional_blocked,
            constitutional_verdict=decision.constitutional_verdict,
            provenance=decision.provenance,
            identity_trusted=decision.identity_trusted,
            identity_authority_multiplier=decision.identity_authority_multiplier,
            coherence_ok=decision.coherence_ok,
            coherence_score=decision.coherence_score,
            coherence_verdict=decision.coherence_verdict,
            metacognitive_reflective=decision.metacognitive_reflective,
            metacognition_score=decision.metacognition_score,
            metacognitive_verdict=decision.metacognitive_verdict,
            homeostasis_stable=decision.homeostasis_stable,
            homeostasis_score=decision.homeostasis_score,
            homeostasis_verdict=decision.homeostasis_verdict,
            stabilization_recommendations=list(decision.stabilization_recommendations),
            external_advisory=decision.external_advisory,
            runtime_external_observability=obs.to_dict(),
            civilization_observability=decision.civilization_observability,
            reality_alignment_observability=decision.reality_alignment_observability,
            temporal_continuity_observability=decision.temporal_continuity_observability,
        )

    def _attach_civilization_observability(
        self,
        decision: GovernanceDecision,
        *,
        route_name: str,
    ) -> GovernanceDecision:
        """Civilization/diplomacy metadata — never overrides acceptance or salience."""
        hints = decision.external_advisory or {}
        payload = " ".join(str(h) for h in hints.get("hints", [])) or route_name
        civ = observe_civilization(
            payload,
            sovereign_id="foreign",
            peer_id="ambient",
            scope="advisory",
            provenance_payload=decision.provenance,
        )
        with_civ = GovernanceDecision(
            accepted=decision.accepted,
            governed_salience=decision.governed_salience,
            arbitration=decision.arbitration,
            reason=decision.reason,
            autonomous_blocked=decision.autonomous_blocked,
            constitutional_compliant=decision.constitutional_compliant,
            constitutional_blocked=decision.constitutional_blocked,
            constitutional_verdict=decision.constitutional_verdict,
            provenance=decision.provenance,
            identity_trusted=decision.identity_trusted,
            identity_authority_multiplier=decision.identity_authority_multiplier,
            coherence_ok=decision.coherence_ok,
            coherence_score=decision.coherence_score,
            coherence_verdict=decision.coherence_verdict,
            metacognitive_reflective=decision.metacognitive_reflective,
            metacognition_score=decision.metacognition_score,
            metacognitive_verdict=decision.metacognitive_verdict,
            homeostasis_stable=decision.homeostasis_stable,
            homeostasis_score=decision.homeostasis_score,
            homeostasis_verdict=decision.homeostasis_verdict,
            stabilization_recommendations=list(decision.stabilization_recommendations),
            external_advisory=decision.external_advisory,
            runtime_external_observability=decision.runtime_external_observability,
            civilization_observability=civ.to_dict(),
            reality_alignment_observability=decision.reality_alignment_observability,
            temporal_continuity_observability=decision.temporal_continuity_observability,
        )
        return self._attach_reality_alignment_observability(
            with_civ, route_name=route_name
        )

    def _attach_reality_alignment_observability(
        self,
        decision: GovernanceDecision,
        *,
        route_name: str,
    ) -> GovernanceDecision:
        """Reality alignment metadata — never overrides acceptance or salience."""
        hints = decision.external_advisory or {}
        payload = " ".join(str(h) for h in hints.get("hints", [])) or route_name
        real = observe_reality_alignment(
            payload,
            left_runtime="ambient",
            right_runtime="foreign",
            scope="advisory",
            provenance_payload=decision.provenance,
        )
        with_real = GovernanceDecision(
            accepted=decision.accepted,
            governed_salience=decision.governed_salience,
            arbitration=decision.arbitration,
            reason=decision.reason,
            autonomous_blocked=decision.autonomous_blocked,
            constitutional_compliant=decision.constitutional_compliant,
            constitutional_blocked=decision.constitutional_blocked,
            constitutional_verdict=decision.constitutional_verdict,
            provenance=decision.provenance,
            identity_trusted=decision.identity_trusted,
            identity_authority_multiplier=decision.identity_authority_multiplier,
            coherence_ok=decision.coherence_ok,
            coherence_score=decision.coherence_score,
            coherence_verdict=decision.coherence_verdict,
            metacognitive_reflective=decision.metacognitive_reflective,
            metacognition_score=decision.metacognition_score,
            metacognitive_verdict=decision.metacognitive_verdict,
            homeostasis_stable=decision.homeostasis_stable,
            homeostasis_score=decision.homeostasis_score,
            homeostasis_verdict=decision.homeostasis_verdict,
            stabilization_recommendations=list(decision.stabilization_recommendations),
            external_advisory=decision.external_advisory,
            runtime_external_observability=decision.runtime_external_observability,
            civilization_observability=decision.civilization_observability,
            reality_alignment_observability=real.to_dict(),
            temporal_continuity_observability=decision.temporal_continuity_observability,
        )
        return self._attach_temporal_continuity_observability(
            with_real, route_name=route_name
        )

    def _attach_temporal_continuity_observability(
        self,
        decision: GovernanceDecision,
        *,
        route_name: str,
    ) -> GovernanceDecision:
        """Temporal continuity metadata — never overrides acceptance or salience."""
        hints = decision.external_advisory or {}
        payload = " ".join(str(h) for h in hints.get("hints", [])) or route_name
        temporal = observe_temporal_continuity(
            payload,
            epoch_id="current",
            runtime_id="ambient",
            scope="advisory",
            provenance_payload=decision.provenance,
        )
        with_temporal = GovernanceDecision(
            accepted=decision.accepted,
            governed_salience=decision.governed_salience,
            arbitration=decision.arbitration,
            reason=decision.reason,
            autonomous_blocked=decision.autonomous_blocked,
            constitutional_compliant=decision.constitutional_compliant,
            constitutional_blocked=decision.constitutional_blocked,
            constitutional_verdict=decision.constitutional_verdict,
            provenance=decision.provenance,
            identity_trusted=decision.identity_trusted,
            identity_authority_multiplier=decision.identity_authority_multiplier,
            coherence_ok=decision.coherence_ok,
            coherence_score=decision.coherence_score,
            coherence_verdict=decision.coherence_verdict,
            metacognitive_reflective=decision.metacognitive_reflective,
            metacognition_score=decision.metacognition_score,
            metacognitive_verdict=decision.metacognitive_verdict,
            homeostasis_stable=decision.homeostasis_stable,
            homeostasis_score=decision.homeostasis_score,
            homeostasis_verdict=decision.homeostasis_verdict,
            stabilization_recommendations=list(decision.stabilization_recommendations),
            external_advisory=decision.external_advisory,
            runtime_external_observability=decision.runtime_external_observability,
            civilization_observability=decision.civilization_observability,
            reality_alignment_observability=decision.reality_alignment_observability,
            temporal_continuity_observability=temporal.to_dict(),
        )
        return self._attach_semantic_continuity_observability(
            with_temporal, route_name=route_name
        )

    def _attach_semantic_continuity_observability(
        self,
        decision: GovernanceDecision,
        *,
        route_name: str,
    ) -> GovernanceDecision:
        """Semantic continuity metadata — never overrides acceptance or salience."""
        hints = decision.external_advisory or {}
        payload = " ".join(str(h) for h in hints.get("hints", [])) or route_name
        semantic = observe_semantic_continuity(
            payload,
            concept_id="current",
            runtime_id="ambient",
            scope="advisory",
            provenance_payload=decision.provenance,
        )
        return self._attach_value_continuity_observability(
            GovernanceDecision(
                accepted=decision.accepted,
                governed_salience=decision.governed_salience,
                arbitration=decision.arbitration,
                reason=decision.reason,
                autonomous_blocked=decision.autonomous_blocked,
                constitutional_compliant=decision.constitutional_compliant,
                constitutional_blocked=decision.constitutional_blocked,
                constitutional_verdict=decision.constitutional_verdict,
                provenance=decision.provenance,
                identity_trusted=decision.identity_trusted,
                identity_authority_multiplier=decision.identity_authority_multiplier,
                coherence_ok=decision.coherence_ok,
                coherence_score=decision.coherence_score,
                coherence_verdict=decision.coherence_verdict,
                metacognitive_reflective=decision.metacognitive_reflective,
                metacognition_score=decision.metacognition_score,
                metacognitive_verdict=decision.metacognitive_verdict,
                homeostasis_stable=decision.homeostasis_stable,
                homeostasis_score=decision.homeostasis_score,
                homeostasis_verdict=decision.homeostasis_verdict,
                stabilization_recommendations=list(decision.stabilization_recommendations),
                external_advisory=decision.external_advisory,
                runtime_external_observability=decision.runtime_external_observability,
                civilization_observability=decision.civilization_observability,
                reality_alignment_observability=decision.reality_alignment_observability,
                temporal_continuity_observability=decision.temporal_continuity_observability,
                semantic_continuity_observability=semantic.to_dict(),
            ),
            route_name=route_name,
        )

    def _attach_value_continuity_observability(
        self,
        decision: GovernanceDecision,
        *,
        route_name: str,
    ) -> GovernanceDecision:
        """Value continuity metadata — never overrides acceptance or salience."""
        hints = decision.external_advisory or {}
        payload = " ".join(str(h) for h in hints.get("hints", [])) or route_name
        value_obs = observe_value_continuity(
            payload,
            value_id="current",
            runtime_id="ambient",
            scope="advisory",
            provenance_payload=decision.provenance,
        )
        return self._attach_intent_continuity_observability(
            GovernanceDecision(
                accepted=decision.accepted,
                governed_salience=decision.governed_salience,
                arbitration=decision.arbitration,
                reason=decision.reason,
                autonomous_blocked=decision.autonomous_blocked,
                constitutional_compliant=decision.constitutional_compliant,
                constitutional_blocked=decision.constitutional_blocked,
                constitutional_verdict=decision.constitutional_verdict,
                provenance=decision.provenance,
                identity_trusted=decision.identity_trusted,
                identity_authority_multiplier=decision.identity_authority_multiplier,
                coherence_ok=decision.coherence_ok,
                coherence_score=decision.coherence_score,
                coherence_verdict=decision.coherence_verdict,
                metacognitive_reflective=decision.metacognitive_reflective,
                metacognition_score=decision.metacognition_score,
                metacognitive_verdict=decision.metacognitive_verdict,
                homeostasis_stable=decision.homeostasis_stable,
                homeostasis_score=decision.homeostasis_score,
                homeostasis_verdict=decision.homeostasis_verdict,
                stabilization_recommendations=list(decision.stabilization_recommendations),
                external_advisory=decision.external_advisory,
                runtime_external_observability=decision.runtime_external_observability,
                civilization_observability=decision.civilization_observability,
                reality_alignment_observability=decision.reality_alignment_observability,
                temporal_continuity_observability=decision.temporal_continuity_observability,
                semantic_continuity_observability=decision.semantic_continuity_observability,
                value_continuity_observability=value_obs.to_dict(),
            ),
            route_name=route_name,
        )

    def _attach_intent_continuity_observability(
        self,
        decision: GovernanceDecision,
        *,
        route_name: str,
    ) -> GovernanceDecision:
        """Intent continuity metadata — never overrides acceptance or salience."""
        hints = decision.external_advisory or {}
        payload = " ".join(str(h) for h in hints.get("hints", [])) or route_name
        intent_obs = observe_intent_continuity(
            payload,
            intent_id="current",
            runtime_id="ambient",
            scope="advisory",
            provenance_payload=decision.provenance,
        )
        return self._attach_purpose_boundary_observability(
            GovernanceDecision(
                accepted=decision.accepted,
                governed_salience=decision.governed_salience,
                arbitration=decision.arbitration,
                reason=decision.reason,
                autonomous_blocked=decision.autonomous_blocked,
                constitutional_compliant=decision.constitutional_compliant,
                constitutional_blocked=decision.constitutional_blocked,
                constitutional_verdict=decision.constitutional_verdict,
                provenance=decision.provenance,
                identity_trusted=decision.identity_trusted,
                identity_authority_multiplier=decision.identity_authority_multiplier,
                coherence_ok=decision.coherence_ok,
                coherence_score=decision.coherence_score,
                coherence_verdict=decision.coherence_verdict,
                metacognitive_reflective=decision.metacognitive_reflective,
                metacognition_score=decision.metacognition_score,
                metacognitive_verdict=decision.metacognitive_verdict,
                homeostasis_stable=decision.homeostasis_stable,
                homeostasis_score=decision.homeostasis_score,
                homeostasis_verdict=decision.homeostasis_verdict,
                stabilization_recommendations=list(decision.stabilization_recommendations),
                external_advisory=decision.external_advisory,
                runtime_external_observability=decision.runtime_external_observability,
                civilization_observability=decision.civilization_observability,
                reality_alignment_observability=decision.reality_alignment_observability,
                temporal_continuity_observability=decision.temporal_continuity_observability,
                semantic_continuity_observability=decision.semantic_continuity_observability,
                value_continuity_observability=decision.value_continuity_observability,
                intent_continuity_observability=intent_obs.to_dict(),
            ),
            route_name=route_name,
        )

    def _attach_purpose_boundary_observability(
        self,
        decision: GovernanceDecision,
        *,
        route_name: str,
    ) -> GovernanceDecision:
        """Purpose boundary metadata — never overrides acceptance or salience."""
        hints = decision.external_advisory or {}
        payload = " ".join(str(h) for h in hints.get("hints", [])) or route_name
        purpose_obs = observe_purpose_boundary(
            payload,
            purpose_id="current",
            runtime_id="ambient",
            scope="advisory",
            provenance_payload=decision.provenance,
        )
        return self._attach_agency_boundary_observability(
            GovernanceDecision(
                accepted=decision.accepted,
                governed_salience=decision.governed_salience,
                arbitration=decision.arbitration,
                reason=decision.reason,
                autonomous_blocked=decision.autonomous_blocked,
                constitutional_compliant=decision.constitutional_compliant,
                constitutional_blocked=decision.constitutional_blocked,
                constitutional_verdict=decision.constitutional_verdict,
                provenance=decision.provenance,
                identity_trusted=decision.identity_trusted,
                identity_authority_multiplier=decision.identity_authority_multiplier,
                coherence_ok=decision.coherence_ok,
                coherence_score=decision.coherence_score,
                coherence_verdict=decision.coherence_verdict,
                metacognitive_reflective=decision.metacognitive_reflective,
                metacognition_score=decision.metacognition_score,
                metacognitive_verdict=decision.metacognitive_verdict,
                homeostasis_stable=decision.homeostasis_stable,
                homeostasis_score=decision.homeostasis_score,
                homeostasis_verdict=decision.homeostasis_verdict,
                stabilization_recommendations=list(decision.stabilization_recommendations),
                external_advisory=decision.external_advisory,
                runtime_external_observability=decision.runtime_external_observability,
                civilization_observability=decision.civilization_observability,
                reality_alignment_observability=decision.reality_alignment_observability,
                temporal_continuity_observability=decision.temporal_continuity_observability,
                semantic_continuity_observability=decision.semantic_continuity_observability,
                value_continuity_observability=decision.value_continuity_observability,
                intent_continuity_observability=decision.intent_continuity_observability,
                purpose_boundary_observability=purpose_obs.to_dict(),
            ),
            route_name=route_name,
        )

    def _attach_agency_boundary_observability(
        self,
        decision: GovernanceDecision,
        *,
        route_name: str,
    ) -> GovernanceDecision:
        """Agency boundary metadata — never overrides acceptance or salience."""
        hints = decision.external_advisory or {}
        payload = " ".join(str(h) for h in hints.get("hints", [])) or route_name
        agency_obs = observe_agency_boundary(
            payload,
            agency_id="current",
            runtime_id="ambient",
            scope="advisory",
            provenance_payload=decision.provenance,
        )
        return GovernanceDecision(
            accepted=decision.accepted,
            governed_salience=decision.governed_salience,
            arbitration=decision.arbitration,
            reason=decision.reason,
            autonomous_blocked=decision.autonomous_blocked,
            constitutional_compliant=decision.constitutional_compliant,
            constitutional_blocked=decision.constitutional_blocked,
            constitutional_verdict=decision.constitutional_verdict,
            provenance=decision.provenance,
            identity_trusted=decision.identity_trusted,
            identity_authority_multiplier=decision.identity_authority_multiplier,
            coherence_ok=decision.coherence_ok,
            coherence_score=decision.coherence_score,
            coherence_verdict=decision.coherence_verdict,
            metacognitive_reflective=decision.metacognitive_reflective,
            metacognition_score=decision.metacognition_score,
            metacognitive_verdict=decision.metacognitive_verdict,
            homeostasis_stable=decision.homeostasis_stable,
            homeostasis_score=decision.homeostasis_score,
            homeostasis_verdict=decision.homeostasis_verdict,
            stabilization_recommendations=list(decision.stabilization_recommendations),
            external_advisory=decision.external_advisory,
            runtime_external_observability=decision.runtime_external_observability,
            civilization_observability=decision.civilization_observability,
            reality_alignment_observability=decision.reality_alignment_observability,
            temporal_continuity_observability=decision.temporal_continuity_observability,
            semantic_continuity_observability=decision.semantic_continuity_observability,
            value_continuity_observability=decision.value_continuity_observability,
            intent_continuity_observability=decision.intent_continuity_observability,
            purpose_boundary_observability=decision.purpose_boundary_observability,
            agency_boundary_observability=agency_obs.to_dict(),
        )

    def _attach_external_advisory(
        self,
        decision: GovernanceDecision,
        *,
        route_name: str,
    ) -> GovernanceDecision:
        """Read-only external skill hints — never overrides acceptance."""
        advisory = self.external_skills.advisory_for_route(route_name)
        with_advisory = GovernanceDecision(
            accepted=decision.accepted,
            governed_salience=decision.governed_salience,
            arbitration=decision.arbitration,
            reason=decision.reason,
            autonomous_blocked=decision.autonomous_blocked,
            constitutional_compliant=decision.constitutional_compliant,
            constitutional_blocked=decision.constitutional_blocked,
            constitutional_verdict=decision.constitutional_verdict,
            provenance=decision.provenance,
            identity_trusted=decision.identity_trusted,
            identity_authority_multiplier=decision.identity_authority_multiplier,
            coherence_ok=decision.coherence_ok,
            coherence_score=decision.coherence_score,
            coherence_verdict=decision.coherence_verdict,
            metacognitive_reflective=decision.metacognitive_reflective,
            metacognition_score=decision.metacognition_score,
            metacognitive_verdict=decision.metacognitive_verdict,
            homeostasis_stable=decision.homeostasis_stable,
            homeostasis_score=decision.homeostasis_score,
            homeostasis_verdict=decision.homeostasis_verdict,
            stabilization_recommendations=list(decision.stabilization_recommendations),
            external_advisory=advisory,
        )
        return self._attach_civilization_observability(
            self._attach_runtime_observability(with_advisory, route_name=route_name),
            route_name=route_name,
        )

    def _register_provenance(
        self,
        target: AttentionTarget,
        *,
        route_name: str,
        raw_confidence: float,
        replay_hint: float,
    ) -> tuple[ProvenanceRecord, IdentityDecision, float]:
        meta = dict(getattr(target, "metadata", None) or {})
        record = self.cognitive_identity.build_record_from_target(
            source_domain=target.source_domain,
            signal_type=target.signal_type,
            route_name=route_name,
            raw_confidence=raw_confidence,
            replay_hint=replay_hint,
            metadata=meta,
        )
        decision = self.cognitive_identity.register(record)
        self.cognitive_coherence.ingest_record(record)
        damped = damp_salience(raw_confidence, record)
        damped = self.synthetic_boundary.bounded_salience(damped, record)
        return record, decision, clamp01(damped * decision.authority_multiplier)

    def _apply_coherence(
        self,
        decision: GovernanceDecision,
        *,
        record: ProvenanceRecord | None = None,
        recent: list[ProvenanceRecord] | None = None,
        route_name: str = "attention_submit",
    ) -> GovernanceDecision:
        """Evaluate coherence after governance, before final output."""
        verdict: CoherenceVerdict = self.cognitive_coherence.evaluate_after_governance(
            governed_salience=decision.governed_salience,
            constitutional_compliant=decision.constitutional_compliant,
            constitutional_verdict=decision.constitutional_verdict,
            identity_trusted=decision.identity_trusted,
            provenance=decision.provenance,
            recent=recent,
        )
        governed = self.cognitive_coherence.damp_salience(
            decision.governed_salience, verdict
        )
        accepted = decision.accepted
        reason = decision.reason
        if not verdict.coherent and accepted:
            if governed < 0.05:
                accepted = False
                reason = "coherence_rejected"
            elif verdict.reasons:
                reason = verdict.reasons[0]
        return self._attach_metacognition(
            GovernanceDecision(
                accepted=accepted,
                governed_salience=governed,
                arbitration=decision.arbitration,
                reason=reason,
                autonomous_blocked=decision.autonomous_blocked,
                constitutional_compliant=decision.constitutional_compliant,
                constitutional_blocked=decision.constitutional_blocked,
                constitutional_verdict=decision.constitutional_verdict,
                provenance=decision.provenance,
                identity_trusted=decision.identity_trusted,
                identity_authority_multiplier=decision.identity_authority_multiplier,
                coherence_ok=verdict.coherent,
                coherence_score=verdict.score,
                coherence_verdict=verdict.to_dict(),
            ),
            route_name=route_name,
        )

    def _attach_metacognition(
        self,
        decision: GovernanceDecision,
        *,
        route_name: str = "attention_submit",
    ) -> GovernanceDecision:
        """Observational meta-cognition + homeostasis after coherence — never overrides."""
        meta: MetacognitiveVerdict = (
            self.metacognitive_reflection.evaluate_after_coherence(
                governed_salience=decision.governed_salience,
                coherence_score=decision.coherence_score,
                coherence_verdict=decision.coherence_verdict,
                constitutional_compliant=decision.constitutional_compliant,
                identity_trusted=decision.identity_trusted,
                accepted=decision.accepted,
                route_name=route_name,
            )
        )
        homeo: HomeostasisVerdict = (
            self.metacognitive_reflection.stabilize_after_reflection(
                meta,
                governed_salience=decision.governed_salience,
                coherence_score=decision.coherence_score,
                coherence_ok=decision.coherence_ok,
                coherence_verdict=decision.coherence_verdict,
            )
        )
        return self._attach_external_advisory(
            GovernanceDecision(
                accepted=decision.accepted,
                governed_salience=decision.governed_salience,
                arbitration=decision.arbitration,
                reason=decision.reason,
                autonomous_blocked=decision.autonomous_blocked,
                constitutional_compliant=decision.constitutional_compliant,
                constitutional_blocked=decision.constitutional_blocked,
                constitutional_verdict=decision.constitutional_verdict,
                provenance=decision.provenance,
                identity_trusted=decision.identity_trusted,
                identity_authority_multiplier=decision.identity_authority_multiplier,
                coherence_ok=decision.coherence_ok,
                coherence_score=decision.coherence_score,
                coherence_verdict=decision.coherence_verdict,
                metacognitive_reflective=meta.reflective,
                metacognition_score=meta.quality_score,
                metacognitive_verdict=meta.to_dict(),
                homeostasis_stable=homeo.stable,
                homeostasis_score=homeo.homeostasis_score,
                homeostasis_verdict=homeo.to_dict(),
                stabilization_recommendations=list(homeo.recommendations),
            ),
            route_name=route_name,
        )

    def _evaluate_constitution(
        self,
        *,
        route_name: str,
        raw_confidence: float,
        uncertainty: float,
        replay_hint: float,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[bool, dict[str, Any] | None]:
        verdict = self.constitutional_guard.evaluate(
            ConstitutionalContext(
                route_name=route_name,
                raw_confidence=raw_confidence,
                uncertainty=uncertainty,
                replay_hint=replay_hint,
                metadata=dict(metadata or {}),
            )
        )
        vdict = verdict.to_dict()
        return verdict.compliant, vdict

    def govern_target(
        self,
        target: AttentionTarget,
        *,
        raw_confidence: float = 0.7,
        uncertainty: float = 0.35,
        replay_hint: float = 0.0,
        route_name: str = "attention_submit",
    ) -> GovernanceDecision:
        if not self.sovereignty.block_recursive_route(route_name):
            return self._apply_coherence(
                GovernanceDecision(
                    accepted=False,
                    governed_salience=0.0,
                    arbitration=ArbitrationResult(
                        final_salience=0.0,
                        arbitration_fairness=0.0,
                        sovereignty_compliant=False,
                        uncertainty_applied=False,
                        replay_bounded=True,
                        somatic_bounded=True,
                        governance_depth=1,
                        trace=["recursive_governance_blocked"],
                    ),
                    reason="recursive_governance_route",
                    autonomous_blocked=True,
                    constitutional_compliant=False,
                    constitutional_blocked=True,
                ),
                route_name=route_name,
            )
        compliant, verdict_dict = self._evaluate_constitution(
            route_name=route_name,
            raw_confidence=raw_confidence,
            uncertainty=uncertainty,
            replay_hint=replay_hint,
            metadata=getattr(target, "metadata", None),
        )
        if not compliant:
            return self._apply_coherence(
                GovernanceDecision(
                    accepted=False,
                    governed_salience=0.0,
                    arbitration=ArbitrationResult(
                        final_salience=0.0,
                        arbitration_fairness=0.0,
                        sovereignty_compliant=True,
                        uncertainty_applied=False,
                        replay_bounded=True,
                        somatic_bounded=True,
                        governance_depth=1,
                        trace=["constitutional_block_before_arbitration"],
                    ),
                    reason="constitutional_violation",
                    autonomous_blocked=True,
                    constitutional_compliant=False,
                    constitutional_blocked=True,
                    constitutional_verdict=verdict_dict,
                ),
                route_name=route_name,
            )
        record, identity_decision, identity_mult = self._register_provenance(
            target,
            route_name=route_name,
            raw_confidence=raw_confidence,
            replay_hint=replay_hint,
        )
        if identity_decision.authority_multiplier <= 0.0:
            return self._apply_coherence(
                GovernanceDecision(
                    accepted=False,
                    governed_salience=0.0,
                    arbitration=ArbitrationResult(
                        final_salience=0.0,
                        arbitration_fairness=0.0,
                        sovereignty_compliant=True,
                        uncertainty_applied=False,
                        replay_bounded=True,
                        somatic_bounded=True,
                        governance_depth=1,
                        trace=["identity_block_before_arbitration"],
                    ),
                    reason=identity_decision.reason,
                    autonomous_blocked=True,
                    constitutional_compliant=True,
                    constitutional_blocked=False,
                    constitutional_verdict=verdict_dict,
                    provenance=record.to_dict(),
                    identity_trusted=identity_decision.trusted,
                    identity_authority_multiplier=0.0,
                ),
                route_name=route_name,
            )
        claims = [
            SalienceClaim(
                domain=target.source_domain,
                salience=float(target.raw_value) * identity_mult,
                confidence=raw_confidence * identity_mult,
            )
        ]
        arb = self.engine.arbitrate(
            claims,
            uncertainty=uncertainty,
            replay_hint=replay_hint,
            replay_confidence=0.4 if replay_hint > 0 else 0.0,
        )
        governed = apply_confidence_cap(arb.final_salience)
        accepted = arb.sovereignty_compliant and governed >= 0.05
        reason = "ok" if accepted else "sovereignty_or_salience_rejected"
        if not identity_decision.trusted and accepted:
            reason = identity_decision.reason
        return self._apply_coherence(
            GovernanceDecision(
                accepted=accepted,
                governed_salience=governed,
                arbitration=arb,
                reason=reason,
                autonomous_blocked=False,
                constitutional_compliant=True,
                constitutional_blocked=False,
                constitutional_verdict=verdict_dict,
                provenance=record.to_dict(),
                identity_trusted=identity_decision.trusted,
                identity_authority_multiplier=identity_decision.authority_multiplier,
            ),
            route_name=route_name,
        )

    def govern_salience(
        self,
        claims: list[SalienceClaim],
        *,
        uncertainty: float = 0.3,
    ) -> GovernanceDecision:
        primary_conf = claims[0].confidence if claims else 0.7
        compliant, verdict_dict = self._evaluate_constitution(
            route_name="salience_arbitration",
            raw_confidence=primary_conf,
            uncertainty=uncertainty,
            replay_hint=0.0,
        )
        if not compliant:
            return self._apply_coherence(
                GovernanceDecision(
                    accepted=False,
                    governed_salience=0.0,
                    arbitration=ArbitrationResult(
                        final_salience=0.0,
                        arbitration_fairness=0.0,
                        sovereignty_compliant=True,
                        uncertainty_applied=False,
                        replay_bounded=True,
                        somatic_bounded=True,
                        governance_depth=1,
                        trace=["constitutional_block_before_arbitration"],
                    ),
                    reason="constitutional_violation",
                    constitutional_compliant=False,
                    constitutional_blocked=True,
                    constitutional_verdict=verdict_dict,
                ),
                route_name="salience_arbitration",
            )
        arb = self.engine.arbitrate(claims, uncertainty=uncertainty)
        governed = apply_confidence_cap(arb.final_salience)
        return self._apply_coherence(
            GovernanceDecision(
                accepted=arb.sovereignty_compliant,
                governed_salience=governed,
                arbitration=arb,
                reason="ok" if arb.sovereignty_compliant else "sovereignty_violation",
                constitutional_compliant=True,
                constitutional_blocked=False,
                constitutional_verdict=verdict_dict,
            ),
            route_name="salience_arbitration",
        )

    def domain_share_score(self, shares: dict[str, float]) -> float:
        return self.sovereignty.compliance_score(shares)
