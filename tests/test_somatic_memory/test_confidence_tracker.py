"""Tests for the somatic confidence tracker (Phase 3)."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from memory.somatic.confidence_tracker import (
    ConfidenceEvent,
    SomaticConfidenceTracker,
)


@pytest.fixture
def tracker(tmp_path: Path) -> SomaticConfidenceTracker:
    return SomaticConfidenceTracker(history_path=str(tmp_path / "conf.jsonl"))


# ── record_initial ────────────────────────────────────────────────────────


class TestRecordInitial:

    def test_creates_event(self, tracker: SomaticConfidenceTracker) -> None:
        event = tracker.record_initial("e1", "episode", 0.6)
        assert isinstance(event, ConfidenceEvent)
        assert event.entity_id == "e1"
        assert event.reason == "initial"

    def test_previous_is_zero(self, tracker: SomaticConfidenceTracker) -> None:
        event = tracker.record_initial("e1", "episode", 0.6)
        assert event.previous_confidence == 0.0

    def test_clamped_to_ceiling(self, tracker: SomaticConfidenceTracker) -> None:
        event = tracker.record_initial("e1", "episode", 1.5)
        assert event.new_confidence <= 0.99

    def test_clamped_to_floor(self, tracker: SomaticConfidenceTracker) -> None:
        event = tracker.record_initial("e1", "episode", -0.5)
        assert event.new_confidence >= 0.01


# ── record_success ────────────────────────────────────────────────────────


class TestRecordSuccess:

    def test_increases_confidence(self, tracker: SomaticConfidenceTracker) -> None:
        event = tracker.record_success("e1", "fingerprint", 0.5)
        assert event.new_confidence > 0.5

    def test_formula_correct(self, tracker: SomaticConfidenceTracker) -> None:
        event = tracker.record_success("e1", "fingerprint", 0.8)
        expected = min(0.8 + 0.05 * (1.0 - 0.8), 0.99)
        assert abs(event.new_confidence - expected) < 1e-6

    def test_never_exceeds_ceiling(self, tracker: SomaticConfidenceTracker) -> None:
        conf = 0.5
        for _ in range(500):
            event = tracker.record_success("e1", "fingerprint", conf)
            conf = event.new_confidence
        assert conf <= 0.99


# ── record_failure ────────────────────────────────────────────────────────


class TestRecordFailure:

    def test_decreases_confidence(self, tracker: SomaticConfidenceTracker) -> None:
        event = tracker.record_failure("e1", "cluster", 0.8)
        assert event.new_confidence < 0.8

    def test_formula_correct(self, tracker: SomaticConfidenceTracker) -> None:
        event = tracker.record_failure("e1", "cluster", 0.5)
        expected = max(0.5 - 0.1 * 0.5, 0.01)
        assert abs(event.new_confidence - expected) < 1e-6

    def test_has_floor(self, tracker: SomaticConfidenceTracker) -> None:
        conf = 0.5
        for _ in range(500):
            event = tracker.record_failure("e1", "cluster", conf)
            conf = event.new_confidence
        assert conf >= 0.01


# ── record_contradiction ──────────────────────────────────────────────────


class TestRecordContradiction:

    def test_applies_penalty(self, tracker: SomaticConfidenceTracker) -> None:
        event = tracker.record_contradiction("e1", "precursor", 0.7, penalty=0.2)
        assert event.new_confidence == pytest.approx(0.5, abs=1e-6)

    def test_has_floor(self, tracker: SomaticConfidenceTracker) -> None:
        event = tracker.record_contradiction("e1", "precursor", 0.05, penalty=0.5)
        assert event.new_confidence >= 0.01

    def test_reason_is_contradiction(self, tracker: SomaticConfidenceTracker) -> None:
        event = tracker.record_contradiction("e1", "precursor", 0.5)
        assert event.reason == "contradiction"


# ── apply_decay ───────────────────────────────────────────────────────────


class TestApplyDecay:

    def test_reduces_over_time(self, tracker: SomaticConfidenceTracker) -> None:
        event = tracker.apply_decay("e1", "episode", 0.8, decay_rate=0.05, elapsed_days=10)
        assert event.new_confidence < 0.8

    def test_formula_correct(self, tracker: SomaticConfidenceTracker) -> None:
        event = tracker.apply_decay("e1", "episode", 0.8, decay_rate=0.1, elapsed_days=5)
        expected = max(0.8 * math.exp(-0.1 * 5), 0.01)
        assert abs(event.new_confidence - expected) < 1e-6

    def test_has_floor(self, tracker: SomaticConfidenceTracker) -> None:
        event = tracker.apply_decay("e1", "episode", 0.5, decay_rate=1.0, elapsed_days=100)
        assert event.new_confidence >= 0.01


# ── get_history ───────────────────────────────────────────────────────────


class TestGetHistory:

    def test_returns_all_events(self, tracker: SomaticConfidenceTracker) -> None:
        tracker.record_initial("e1", "episode", 0.5)
        tracker.record_success("e1", "episode", 0.5)
        tracker.record_failure("e1", "episode", 0.525)
        tracker.record_initial("e2", "fingerprint", 0.3)

        history = tracker.get_history("e1")
        assert len(history) == 3
        assert all(e.entity_id == "e1" for e in history)

    def test_empty_for_unknown_entity(self, tracker: SomaticConfidenceTracker) -> None:
        assert tracker.get_history("nonexistent") == []


# ── get_current_confidence ────────────────────────────────────────────────


class TestGetCurrentConfidence:

    def test_returns_latest(self, tracker: SomaticConfidenceTracker) -> None:
        tracker.record_initial("e1", "episode", 0.5)
        event = tracker.record_success("e1", "episode", 0.5)
        assert tracker.get_current_confidence("e1") == event.new_confidence

    def test_none_for_unknown(self, tracker: SomaticConfidenceTracker) -> None:
        assert tracker.get_current_confidence("nope") is None


# ── Persistence ───────────────────────────────────────────────────────────


class TestConfidencePersistence:

    def test_save_load_roundtrip(self, tmp_path: Path) -> None:
        path = str(tmp_path / "hist.jsonl")

        t1 = SomaticConfidenceTracker(history_path=path)
        t1.record_initial("e1", "episode", 0.6)
        t1.record_success("e1", "episode", 0.6)

        t2 = SomaticConfidenceTracker(history_path=path)
        assert len(t2.get_history("e1")) == 2
        assert t2.get_current_confidence("e1") is not None
