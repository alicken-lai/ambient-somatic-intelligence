"""L2→L3 Clustering Stress Test.

Verifies that instinct clusters are correctly promoted to skill candidates,
enforcing min_success_rate, cross_context requirements, and governance.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from memory.ontology.layer_definition import MemoryLayer
from memory.ontology.instinct_schema import InstinctEntry
from memory.ontology.promotion_rules import PROMOTION_RULES, check_promotion_eligibility
from memory.ontology.confidence_model import ConfidenceModel
from memory.ontology.promotion_engine import PromotionEngine


L2_TO_L3_RULE = PROMOTION_RULES[1]


def _make_instinct(
    confidence: float = 0.85,
    occurrence_count: int = 6,
    success_count: int = 5,
    failure_count: int = 1,
    contexts: list[str] | None = None,
) -> InstinctEntry:
    return InstinctEntry(
        entry_id=f"inst-cluster-{uuid.uuid4().hex[:6]}",
        timestamp=datetime.now(timezone.utc),
        source_episodes=[f"ep-{i}" for i in range(5)],
        observation="Thermal drift pattern detected",
        trigger_conditions=["thermal_drift", "fan_mismatch"],
        confidence=confidence,
        contextual_applicability=contexts or ["rack_a", "rack_b"],
        occurrence_count=occurrence_count,
        success_count=success_count,
        failure_count=failure_count,
        last_validated=datetime.now(timezone.utc),
    )


class TestInstinctsClusterIntoSkillCandidate:
    def test_instincts_cluster_into_skill_candidate(self, promotion_engine):
        """Well-formed instincts should produce eligible L3 candidates."""
        instincts = [_make_instinct() for _ in range(5)]
        candidates = promotion_engine.scan_candidates(instincts, MemoryLayer.L2_INSTINCT)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) == 5
        for c in eligible:
            assert c.target_layer == MemoryLayer.L3_SKILL


class TestMinSuccessRateEnforced:
    def test_min_success_rate_enforced(self, promotion_engine):
        """Instinct with success_rate < 0.7 should not be eligible for L3."""
        low_sr_instinct = _make_instinct(
            success_count=2,
            failure_count=8,
        )
        assert low_sr_instinct.success_rate() < 0.7
        candidates = promotion_engine.scan_candidates([low_sr_instinct], MemoryLayer.L2_INSTINCT)
        for c in candidates:
            assert not c.eligible
            assert any("Success rate" in r for r in c.blocking_reasons)


class TestCrossContextRequired:
    def test_cross_context_required(self, promotion_engine):
        """Instinct with only one context should not be eligible for L3."""
        single_ctx = _make_instinct(contexts=["only_one_context"])
        candidates = promotion_engine.scan_candidates([single_ctx], MemoryLayer.L2_INSTINCT)
        for c in candidates:
            assert not c.eligible
            assert any("Cross-context" in r for r in c.blocking_reasons)


class TestGovernanceRequiredForL3:
    def test_governance_required_for_l3(self, promotion_engine):
        """L2→L3 rule requires governance — approve_promotion without gov ID should fail."""
        instinct = _make_instinct()
        candidates = promotion_engine.scan_candidates([instinct], MemoryLayer.L2_INSTINCT)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) > 0
        promotion_engine.propose_promotion(eligible[0])
        result = promotion_engine.approve_promotion(
            eligible[0].candidate_id,
            governance_decision_id="",
        )
        assert not result.approved
        assert "Governance" in result.reason


class TestSkillCandidateHasEvidence:
    def test_skill_candidate_has_evidence(self, promotion_engine):
        """Promotion candidate must carry evidence dict with key metrics."""
        instinct = _make_instinct()
        candidates = promotion_engine.scan_candidates([instinct], MemoryLayer.L2_INSTINCT)
        assert len(candidates) > 0
        c = candidates[0]
        assert "confidence" in c.evidence
        assert "occurrence_count" in c.evidence
        assert "success_rate" in c.evidence
        assert "cross_contexts" in c.evidence
