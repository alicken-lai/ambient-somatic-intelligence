"""Ontology contract validation tests.

Verifies that the ontology layer's internal contracts are correct:
schemas round-trip, promotion rules chain properly, decay ordering
is correct, and governance requirements are respected.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from memory.ontology import (
    ConfidenceModel,
    DecayEngine,
    DecayReport,
    DecayRule,
    DECAY_RULES,
    DECAY_RULE_REGISTRY,
    EpisodicEntry,
    InstinctEntry,
    LAYER_REGISTRY,
    MemoryLayer,
    PROMOTION_RULES,
    PromotionCandidate,
    PromotionEngine,
    PromotionResult,
    PromotionRule,
    SkillMemoryEntry,
    StrategicEntry,
)


class TestSchemaRoundTrip:
    """Test each schema round-trips through to_dict/from_dict."""

    def test_episodic_entry_round_trip(self):
        now = datetime.now(timezone.utc)
        entry = EpisodicEntry(
            entry_id="ep-rt-001",
            timestamp=now,
            source="integration_test",
            content="round-trip test",
            tags=["test", "roundtrip"],
            signal_types=["cpu_spike", "mem_pressure"],
            environmental_context={"cpu": 0.9, "mem": 0.7},
            confidence=0.82,
            access_count=3,
            last_accessed=now,
            linked_entries=["ep-rt-000"],
        )
        data = entry.to_dict()
        restored = EpisodicEntry.from_dict(data)

        assert restored.entry_id == entry.entry_id
        assert restored.confidence == entry.confidence
        assert restored.tags == entry.tags
        assert restored.access_count == entry.access_count
        assert restored.layer == MemoryLayer.L1_EPISODIC

    def test_instinct_entry_round_trip(self):
        now = datetime.now(timezone.utc)
        entry = InstinctEntry(
            entry_id="inst-rt-001",
            timestamp=now,
            source_episodes=["ep-001", "ep-002", "ep-003"],
            observation="CPU spikes precede OOM within 30s",
            trigger_conditions=["cpu > 90%", "mem > 80%"],
            confidence=0.78,
            contextual_applicability=["web-server", "batch-job"],
            occurrence_count=7,
            success_count=5,
            failure_count=2,
            last_validated=now,
            contradiction_count=1,
        )
        data = entry.to_dict()
        restored = InstinctEntry.from_dict(data)

        assert restored.entry_id == entry.entry_id
        assert restored.source_episodes == entry.source_episodes
        assert restored.confidence == entry.confidence
        assert restored.occurrence_count == entry.occurrence_count
        assert restored.layer == MemoryLayer.L2_INSTINCT
        assert restored.success_rate() == pytest.approx(5 / 7)

    def test_skill_memory_entry_round_trip(self):
        now = datetime.now(timezone.utc)
        entry = SkillMemoryEntry(
            entry_id="skill-rt-001",
            timestamp=now,
            source_instincts=["inst-001", "inst-002"],
            skill_name="preemptive_gc",
            description="Preemptively trigger GC before OOM",
            workflow_steps=["detect_pressure", "trigger_gc", "verify_recovery"],
            confidence=0.88,
            execution_count=15,
            success_count=13,
            failure_count=2,
            avg_duration_ms=250.0,
            contexts_validated=["production", "staging", "dev"],
            linked_skill_id="skill-ext-001",
            last_executed=now,
        )
        data = entry.to_dict()
        restored = SkillMemoryEntry.from_dict(data)

        assert restored.entry_id == entry.entry_id
        assert restored.skill_name == entry.skill_name
        assert restored.workflow_steps == entry.workflow_steps
        assert restored.contexts_validated == entry.contexts_validated
        assert restored.layer == MemoryLayer.L3_SKILL
        assert restored.success_rate() == pytest.approx(13 / 15)

    def test_strategic_entry_round_trip(self):
        now = datetime.now(timezone.utc)
        entry = StrategicEntry(
            entry_id="strat-rt-001",
            timestamp=now,
            source_skills=["skill-001", "skill-002"],
            heuristic="Always preempt OOM; never wait for the kill signal",
            applicability_scope="all_services",
            confidence=0.93,
            validation_count=20,
            cross_project_validations=["proj-A", "proj-B", "proj-C"],
            governance_approval_id="gov-decision-001",
            verifier_id="guardian-agent",
            last_applied=now,
            contradiction_count=0,
        )
        data = entry.to_dict()
        restored = StrategicEntry.from_dict(data)

        assert restored.entry_id == entry.entry_id
        assert restored.heuristic == entry.heuristic
        assert restored.governance_approval_id == entry.governance_approval_id
        assert restored.verifier_id == entry.verifier_id
        assert restored.layer == MemoryLayer.L4_STRATEGIC
        assert restored.is_valid() is True


class TestPromotionRulesChain:
    """Test promotion rules chain correctly L1→L2→L3→L4."""

    def test_rules_form_complete_chain(self):
        layers_covered = [(r.source_layer, r.target_layer) for r in PROMOTION_RULES]
        assert (MemoryLayer.L1_EPISODIC, MemoryLayer.L2_INSTINCT) in layers_covered
        assert (MemoryLayer.L2_INSTINCT, MemoryLayer.L3_SKILL) in layers_covered
        assert (MemoryLayer.L3_SKILL, MemoryLayer.L4_STRATEGIC) in layers_covered

    def test_rules_have_increasing_requirements(self):
        l1_to_l2 = PROMOTION_RULES[0]
        l2_to_l3 = PROMOTION_RULES[1]
        l3_to_l4 = PROMOTION_RULES[2]

        assert l1_to_l2.min_confidence < l2_to_l3.min_confidence < l3_to_l4.min_confidence
        assert l1_to_l2.min_occurrences < l2_to_l3.min_occurrences < l3_to_l4.min_occurrences

    def test_governance_escalates_with_layer(self):
        l1_to_l2 = PROMOTION_RULES[0]
        l2_to_l3 = PROMOTION_RULES[1]
        l3_to_l4 = PROMOTION_RULES[2]

        assert l1_to_l2.requires_governance is False
        assert l2_to_l3.requires_governance is True
        assert l3_to_l4.requires_governance is True
        assert l3_to_l4.requires_verifier is True

    def test_cross_context_required_for_l3_and_l4(self):
        l1_to_l2 = PROMOTION_RULES[0]
        l2_to_l3 = PROMOTION_RULES[1]
        l3_to_l4 = PROMOTION_RULES[2]

        assert l1_to_l2.requires_cross_context is False
        assert l2_to_l3.requires_cross_context is True
        assert l3_to_l4.requires_cross_context is True


class TestDecayRulesOrdering:
    """Test decay rules are ordered by severity (L1 fastest, L4 slowest)."""

    def test_decay_rates_decrease_with_layer(self):
        rates = [DECAY_RULE_REGISTRY[MemoryLayer(i)].base_rate_per_day for i in range(1, 5)]
        for i in range(len(rates) - 1):
            assert rates[i] > rates[i + 1], (
                f"L{i+1} rate ({rates[i]}) should be > L{i+2} rate ({rates[i+1]})"
            )

    def test_inactivity_thresholds_increase_with_layer(self):
        thresholds = [DECAY_RULE_REGISTRY[MemoryLayer(i)].inactivity_threshold_days for i in range(1, 5)]
        for i in range(len(thresholds) - 1):
            assert thresholds[i] < thresholds[i + 1], (
                f"L{i+1} threshold ({thresholds[i]}) should be < L{i+2} threshold ({thresholds[i+1]})"
            )

    def test_min_confidence_floors_increase_with_layer(self):
        floors = [DECAY_RULE_REGISTRY[MemoryLayer(i)].min_confidence for i in range(1, 5)]
        for i in range(len(floors) - 1):
            assert floors[i] < floors[i + 1], (
                f"L{i+1} floor ({floors[i]}) should be < L{i+2} floor ({floors[i+1]})"
            )

    def test_all_four_layers_have_decay_rules(self):
        assert len(DECAY_RULES) == 4
        for layer in MemoryLayer:
            assert layer in DECAY_RULE_REGISTRY


class TestConfidenceModelLayerFloors:
    """Test confidence model respects layer-specific floors."""

    def test_episodic_floor(self):
        model = ConfidenceModel()
        rule = DECAY_RULE_REGISTRY[MemoryLayer.L1_EPISODIC]
        entry = EpisodicEntry(
            entry_id="ep-floor-001",
            timestamp=datetime.now(timezone.utc),
            source="test", content="test", tags=[], signal_types=[],
            environmental_context={}, confidence=0.05,
        )
        model.apply_decay(entry, elapsed_days=100, rule=rule)
        assert entry.confidence >= rule.min_confidence

    def test_strategic_floor(self):
        model = ConfidenceModel()
        rule = DECAY_RULE_REGISTRY[MemoryLayer.L4_STRATEGIC]
        entry = StrategicEntry(
            entry_id="strat-floor-001",
            timestamp=datetime.now(timezone.utc),
            source_skills=[], heuristic="test", applicability_scope="test",
            confidence=0.25,
        )
        model.apply_decay(entry, elapsed_days=1000, rule=rule)
        assert entry.confidence >= rule.min_confidence

    def test_contradiction_respects_floor(self):
        model = ConfidenceModel()
        rule = DECAY_RULE_REGISTRY[MemoryLayer.L2_INSTINCT]
        entry = InstinctEntry(
            entry_id="inst-floor-001",
            timestamp=datetime.now(timezone.utc),
            source_episodes=[], observation="test",
            trigger_conditions=[], confidence=0.06,
        )
        model.update_on_contradiction(entry, "test", rule=rule)
        assert entry.confidence >= rule.min_confidence


class TestPromotionEngineGovernance:
    """Test PromotionEngine respects governance requirements."""

    def _make_engine(self):
        model = ConfidenceModel()
        return PromotionEngine(rules=PROMOTION_RULES, confidence_model=model)

    def _make_eligible_instinct(self):
        return InstinctEntry(
            entry_id="inst-gov-001",
            timestamp=datetime.now(timezone.utc),
            source_episodes=["ep-1", "ep-2", "ep-3"],
            observation="Pattern detected",
            trigger_conditions=["condition"],
            confidence=0.85,
            contextual_applicability=["ctx-A", "ctx-B"],
            occurrence_count=10,
            success_count=8,
            failure_count=2,
        )

    def _make_eligible_skill(self):
        return SkillMemoryEntry(
            entry_id="skill-gov-001",
            timestamp=datetime.now(timezone.utc),
            source_instincts=["inst-1"],
            skill_name="test_skill",
            description="test",
            workflow_steps=["step1"],
            confidence=0.92,
            execution_count=15,
            success_count=13,
            failure_count=2,
            contexts_validated=["ctx-A", "ctx-B", "ctx-C"],
        )

    def test_l2_to_l3_requires_governance_decision_id(self):
        engine = self._make_engine()
        entry = self._make_eligible_instinct()
        candidates = engine.scan_candidates([entry], MemoryLayer.L2_INSTINCT)
        assert len(candidates) == 1

        candidate = candidates[0]
        assert candidate.eligible is True
        engine.propose_promotion(candidate)

        result = engine.approve_promotion(candidate.candidate_id, governance_decision_id="")
        assert result.approved is False
        assert "Governance decision ID is required" in result.reason

    def test_l3_to_l4_requires_verifier_id(self):
        engine = self._make_engine()
        entry = self._make_eligible_skill()
        candidates = engine.scan_candidates([entry], MemoryLayer.L3_SKILL)
        assert len(candidates) == 1

        candidate = candidates[0]
        assert candidate.eligible is True
        engine.propose_promotion(candidate)

        result = engine.approve_promotion(
            candidate.candidate_id,
            governance_decision_id="gov-001",
            verifier_id=None,
        )
        assert result.approved is False
        assert "verifier_id" in result.reason

    def test_l3_to_l4_succeeds_with_full_governance(self):
        engine = self._make_engine()
        entry = self._make_eligible_skill()
        candidates = engine.scan_candidates([entry], MemoryLayer.L3_SKILL)
        candidate = candidates[0]
        engine.propose_promotion(candidate)

        result = engine.approve_promotion(
            candidate.candidate_id,
            governance_decision_id="gov-001",
            verifier_id="guardian-agent",
        )
        assert result.approved is True
        assert result.new_entry_id is not None

    def test_promotion_is_auditable(self):
        engine = self._make_engine()
        entry = self._make_eligible_instinct()
        candidates = engine.scan_candidates([entry], MemoryLayer.L2_INSTINCT)
        candidate = candidates[0]
        engine.propose_promotion(candidate)
        engine.approve_promotion(candidate.candidate_id, governance_decision_id="gov-123")

        audit = engine.audit_log()
        assert len(audit) >= 2
        actions = [a["action"] for a in audit]
        assert "proposed" in actions
        assert "approved" in actions

    def test_promotion_is_reversible(self):
        engine = self._make_engine()
        entry = self._make_eligible_instinct()
        candidates = engine.scan_candidates([entry], MemoryLayer.L2_INSTINCT)
        candidate = candidates[0]
        engine.propose_promotion(candidate)
        result = engine.approve_promotion(candidate.candidate_id, governance_decision_id="gov-456")
        assert result.approved is True

        rolled_back = engine.rollback_promotion(result)
        assert rolled_back is True
        assert result.approved is False


class TestDecayEngineReports:
    """Test DecayEngine reports are human-readable."""

    def test_empty_report(self):
        model = ConfidenceModel()
        engine = DecayEngine(rules=DECAY_RULES, confidence_model=model)
        text = engine.generate_report([])
        assert "no entries affected" in text

    def test_report_with_entries(self):
        model = ConfidenceModel()
        engine = DecayEngine(rules=DECAY_RULES, confidence_model=model)

        now = datetime.now(timezone.utc)
        past = now - timedelta(days=30)
        entries = [
            EpisodicEntry(
                entry_id=f"ep-rep-{i:03d}", timestamp=past, source="test",
                content="test", tags=[], signal_types=[],
                environmental_context={}, confidence=0.5,
            )
            for i in range(3)
        ]
        reports = engine.apply_time_decay(entries, now)
        text = engine.generate_report(reports)

        assert "Decay Report" in text
        assert "3 entries affected" in text
        assert any(action in text for action in ["REMOVE", "ARCHIVE", "RETAIN"])

    def test_report_contains_entry_ids(self):
        model = ConfidenceModel()
        engine = DecayEngine(rules=DECAY_RULES, confidence_model=model)

        now = datetime.now(timezone.utc)
        past = now - timedelta(days=15)
        entry = EpisodicEntry(
            entry_id="ep-specific-id", timestamp=past, source="test",
            content="test", tags=[], signal_types=[],
            environmental_context={}, confidence=0.6,
        )
        reports = engine.apply_time_decay([entry], now)
        text = engine.generate_report(reports)
        assert "ep-specific-id" in text
