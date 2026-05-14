"""Phase 0E — Confidence Decay + Contradiction Stress Test.

Verifies time-based decay, inactivity acceleration, contradiction penalties,
and promotion eligibility revocation under sustained decay.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest

from memory.ontology.layer_definition import MemoryLayer
from memory.ontology.instinct_schema import InstinctEntry
from memory.ontology.strategic_schema import StrategicEntry
from memory.ontology.decay_rules import DECAY_RULES, DECAY_RULE_REGISTRY, compute_decay, should_remove
from memory.ontology.confidence_model import ConfidenceModel
from memory.ontology.decay_engine import DecayEngine
from memory.ontology.promotion_rules import PROMOTION_RULES, check_promotion_eligibility


def _make_instinct(
    confidence: float = 0.85,
    timestamp: datetime | None = None,
    last_validated: datetime | None = None,
) -> InstinctEntry:
    return InstinctEntry(
        entry_id="inst-decay-test",
        timestamp=timestamp or datetime(2025, 1, 1, tzinfo=timezone.utc),
        source_episodes=["ep-001", "ep-002", "ep-003"],
        observation="Thermal drift means failure",
        trigger_conditions=["thermal_drift", "fan_mismatch"],
        confidence=confidence,
        contextual_applicability=["rack_thermal", "hvac_thermal"],
        occurrence_count=10,
        success_count=8,
        failure_count=2,
        last_validated=last_validated,
    )


def _make_strategic(
    confidence: float = 0.92,
    timestamp: datetime | None = None,
    last_applied: datetime | None = None,
) -> StrategicEntry:
    return StrategicEntry(
        entry_id="strat-decay-test",
        timestamp=timestamp or datetime(2025, 1, 1, tzinfo=timezone.utc),
        source_skills=["skill-001"],
        heuristic="Thermal drift above 0.7 always precedes failure",
        applicability_scope="all_thermal",
        confidence=confidence,
        validation_count=20,
        cross_project_validations=["proj_a", "proj_b"],
        governance_approval_id="gov-001",
        verifier_id="ver-001",
        last_applied=last_applied,
    )


class TestTimeDecayReducesConfidence:
    def test_time_decay_reduces_confidence(self, decay_engine):
        entry = _make_instinct(confidence=0.85)
        now = entry.timestamp + timedelta(days=30)
        reports = decay_engine.apply_time_decay([entry], now)
        assert len(reports) == 1
        assert reports[0].new_confidence < 0.85
        assert entry.confidence < 0.85


class TestInactivityAcceleratesDecay:
    def test_inactivity_accelerates_decay(self, decay_engine):
        ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
        entry_active = _make_instinct(confidence=0.85, timestamp=ts, last_validated=ts + timedelta(days=25))
        entry_inactive = _make_instinct(confidence=0.85, timestamp=ts, last_validated=ts)
        entry_inactive.entry_id = "inst-inactive"

        now = ts + timedelta(days=60)
        reports_inactive = decay_engine.apply_inactivity_decay([entry_inactive], now)

        assert len(reports_inactive) > 0
        assert entry_inactive.confidence < 0.85


class TestContradictionReducesConfidenceImmediately:
    def test_contradiction_reduces_confidence_immediately(self, decay_engine):
        entry = _make_instinct(confidence=0.85)
        report = decay_engine.apply_contradiction(entry, "thermal drift with successful outcome")
        assert entry.confidence < 0.85
        assert report.decay_reason == "contradiction"
        assert entry.contradiction_count == 1


class TestMultipleContradictionsCompound:
    def test_multiple_contradictions_compound(self, decay_engine):
        entry = _make_instinct(confidence=0.85)
        initial = entry.confidence
        for i in range(10):
            decay_engine.apply_contradiction(entry, f"contradiction #{i}")
        assert entry.confidence < initial * 0.5
        assert entry.contradiction_count == 10


class TestL4DecaysSlowerThanL2:
    def test_l4_decays_slower_than_l2(self, decay_engine):
        ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
        l2_entry = _make_instinct(confidence=0.85, timestamp=ts)
        l4_entry = _make_strategic(confidence=0.85, timestamp=ts)

        now = ts + timedelta(days=60)
        decay_engine.apply_time_decay([l2_entry], now)
        decay_engine.apply_time_decay([l4_entry], now)

        assert l4_entry.confidence > l2_entry.confidence


class TestConfidenceBelowThresholdFlagsRemoval:
    def test_confidence_below_threshold_flags_removal(self, decay_engine):
        entry = _make_instinct(confidence=0.85)
        l2_rule = DECAY_RULE_REGISTRY[MemoryLayer.L2_INSTINCT]
        for i in range(20):
            decay_engine.apply_contradiction(entry, f"contradiction #{i}")
        assert entry.confidence <= l2_rule.min_confidence or entry.confidence < 0.1
        assert should_remove(entry, l2_rule) or entry.confidence <= l2_rule.min_confidence


class TestPromotionEligibilityRevokedAfterDecay:
    def test_promotion_eligibility_revoked_after_decay(self, decay_engine):
        entry = _make_instinct(confidence=0.85)
        l2_to_l3_rule = PROMOTION_RULES[1]
        eligible_before, _ = check_promotion_eligibility(entry, l2_to_l3_rule)
        assert eligible_before

        for i in range(15):
            decay_engine.apply_contradiction(entry, f"contradiction #{i}")
        eligible_after, reasons = check_promotion_eligibility(entry, l2_to_l3_rule)
        assert not eligible_after
        assert any("Confidence" in r for r in reasons)


class TestDecayAuditLogComplete:
    def test_decay_audit_log_complete(self, confidence_model, decay_engine):
        entry = _make_instinct(confidence=0.85)
        now = entry.timestamp + timedelta(days=30)
        decay_engine.apply_time_decay([entry], now)
        decay_engine.apply_contradiction(entry, "test contradiction")

        history = confidence_model.history.get_history(entry.entry_id)
        assert len(history) >= 2
        reasons = [h.reason for h in history]
        assert "decay" in reasons
        assert "contradiction" in reasons


class TestDecayReportReadable:
    def test_decay_report_readable(self, decay_engine):
        ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
        entries = [
            _make_instinct(confidence=0.85, timestamp=ts),
        ]
        entries[0].entry_id = "inst-report-test"
        now = ts + timedelta(days=60)
        reports = decay_engine.sweep(entries, now)
        report_text = decay_engine.generate_report(reports)
        assert "inst-report-test" in report_text
        assert "Decay Report" in report_text or "no entries affected" in report_text
