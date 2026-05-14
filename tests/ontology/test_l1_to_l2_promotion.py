"""Phase 0C — L1→L2 Instinct Formation Stress Test.

Simulates 20 repeated thermal drift events and verifies instinct formation
through the PromotionEngine pipeline.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from memory.ontology.layer_definition import MemoryLayer, LAYER_REGISTRY
from memory.ontology.episodic_schema import EpisodicEntry
from memory.ontology.instinct_schema import InstinctEntry
from memory.ontology.promotion_rules import PROMOTION_RULES, check_promotion_eligibility
from memory.ontology.confidence_model import ConfidenceModel
from memory.ontology.promotion_engine import PromotionEngine, PromotionCandidate


SIGNAL_TYPES = ["thermal_drift", "fan_mismatch", "humidity_fluctuation", "power_ripple"]


def _make_thermal_episodes(n: int = 20) -> list[EpisodicEntry]:
    """Generate n EpisodicEntry objects simulating thermal drift."""
    base_time = datetime(2025, 6, 1, tzinfo=timezone.utc)
    entries = []
    for i in range(n):
        entries.append(EpisodicEntry(
            entry_id=f"ep-thermal-{i:04d}",
            timestamp=base_time + timedelta(hours=i * 2),
            source="thermal_sensor",
            content=f"Thermal drift event #{i} detected",
            tags=["thermal", "drift", "recurring"],
            signal_types=SIGNAL_TYPES,
            environmental_context={
                "cpu_band": "heavy",
                "memory_band": "moderate",
                "disk_band": "idle",
            },
            confidence=1.0,
            access_count=i + 1,
        ))
    return entries


class TestThermalDriftEpisodesCreateL1Entries:
    def test_thermal_drift_episodes_create_l1_entries(self):
        entries = _make_thermal_episodes(20)
        assert len(entries) == 20
        for entry in entries:
            assert entry.layer == MemoryLayer.L1_EPISODIC
            assert "thermal_drift" in entry.signal_types
            assert entry.confidence == 1.0
            assert entry.environmental_context["cpu_band"] == "heavy"


class TestRepeatedPatternsGenerateL2Candidates:
    def test_repeated_patterns_generate_l2_candidates(self, promotion_engine):
        entries = _make_thermal_episodes(20)
        candidates = promotion_engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        assert len(candidates) > 0
        eligible_candidates = [c for c in candidates if c.eligible]
        assert len(eligible_candidates) > 0
        for c in eligible_candidates:
            assert c.source_layer == MemoryLayer.L1_EPISODIC
            assert c.target_layer == MemoryLayer.L2_INSTINCT


class TestConfidenceRisesWithValidation:
    def test_confidence_rises_with_validation(self, confidence_model, make_instinct_entry):
        entry = make_instinct_entry(confidence=0.7)
        initial_conf = entry.confidence
        for _ in range(5):
            confidence_model.update_on_success(entry)
        assert entry.confidence > initial_conf


class TestOccurrenceCountIncreases:
    def test_occurrence_count_increases(self):
        entry = InstinctEntry(
            entry_id="inst-occ-test",
            timestamp=datetime.now(timezone.utc),
            source_episodes=["ep-001", "ep-002", "ep-003"],
            observation="Thermal drift correlates with failure",
            trigger_conditions=["thermal_drift"],
            confidence=0.8,
            occurrence_count=3,
        )
        entry.occurrence_count += 1
        assert entry.occurrence_count == 4
        entry.occurrence_count += 5
        assert entry.occurrence_count == 9


class TestPromotionBlockedBelowThreshold:
    def test_promotion_blocked_below_threshold(self, promotion_engine):
        """With access_count=2 (<3 required), should NOT be eligible."""
        entries = [
            EpisodicEntry(
                entry_id=f"ep-below-{i}",
                timestamp=datetime.now(timezone.utc),
                source="test",
                content="Low occurrence entry",
                tags=["test"],
                signal_types=["thermal_drift"],
                environmental_context={"cpu_band": "heavy"},
                confidence=0.8,
                access_count=2,
            )
            for i in range(2)
        ]
        candidates = promotion_engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        for c in candidates:
            assert not c.eligible
            assert any("Occurrences" in r for r in c.blocking_reasons)


class TestPromotionAllowedAtThreshold:
    def test_promotion_allowed_at_threshold(self, promotion_engine):
        """With access_count=3 (>=3 required) and confidence>=0.7, should be eligible."""
        entries = [
            EpisodicEntry(
                entry_id=f"ep-at-thresh-{i}",
                timestamp=datetime.now(timezone.utc),
                source="test",
                content="Threshold entry",
                tags=["test"],
                signal_types=["thermal_drift"],
                environmental_context={"cpu_band": "heavy"},
                confidence=0.8,
                access_count=3,
            )
            for i in range(5)
        ]
        candidates = promotion_engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) == 5


class TestClusterAssignmentStableAcrossRepeats:
    def test_cluster_assignment_stable_across_repeats(self, promotion_engine):
        """Multiple scans of the same entries should produce consistent candidates."""
        entries = _make_thermal_episodes(10)
        candidates_1 = promotion_engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        candidates_2 = promotion_engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)

        eligible_1 = {c.entry_id for c in candidates_1 if c.eligible}
        eligible_2 = {c.entry_id for c in candidates_2 if c.eligible}
        assert eligible_1 == eligible_2


class TestInstinctFormationReportGenerated:
    def test_instinct_formation_report_generated(self, promotion_engine):
        """Full pipeline: scan → propose → approve, verify audit log."""
        entries = _make_thermal_episodes(20)
        candidates = promotion_engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) > 0

        candidate = eligible[0]
        promotion_engine.propose_promotion(candidate)
        result = promotion_engine.approve_promotion(
            candidate.candidate_id,
            governance_decision_id="gov-stress-test-001",
        )
        assert result.approved
        assert result.new_entry_id is not None

        audit = promotion_engine.audit_log()
        assert len(audit) >= 2
        actions = [a["action"] for a in audit]
        assert "proposed" in actions
        assert "approved" in actions
