"""Tests for attention.novelty_detector — Novelty detection, habituation."""

from __future__ import annotations

from attention.attention_state import AttentionSignal
from attention.novelty_detector import NoveltyDetector


def _make_signal(
    domain: str = "somatic",
    signal_type: str = "cpu_spike",
    raw_value: float = 0.5,
) -> AttentionSignal:
    return AttentionSignal(
        source_domain=domain,
        signal_type=signal_type,
        raw_value=raw_value,
    )


def test_first_occurrence_novel() -> None:
    """First signal is highly novel (score ~1.0)."""
    detector = NoveltyDetector()
    signal = _make_signal(signal_type="brand_new")
    score = detector.detect(signal)

    assert score.is_first_occurrence is True
    assert score.score == 1.0
    assert score.occurrence_count == 1


def test_habituation() -> None:
    """Repeated signals become less novel over time."""
    detector = NoveltyDetector()

    scores = []
    for _ in range(10):
        sig = _make_signal(signal_type="recurring")
        score = detector.detect(sig)
        scores.append(score.score)

    assert scores[0] > scores[-1], "Novelty should decrease with repetition"
    assert scores[-1] < 0.5, "After 10 occurrences, novelty should be low"


def test_temporal_window() -> None:
    """Different signal types maintain independent novelty counters."""
    detector = NoveltyDetector()

    for _ in range(5):
        detector.detect(_make_signal(signal_type="type_a"))

    fresh = detector.detect(_make_signal(signal_type="type_b"))
    assert fresh.is_first_occurrence is True
    assert fresh.score == 1.0


def test_novelty_score_fields() -> None:
    """NoveltyScore has all expected fields."""
    detector = NoveltyDetector()
    signal = _make_signal()
    score = detector.detect(signal)

    assert score.signal_id == signal.signal_id
    assert isinstance(score.score, float)
    assert isinstance(score.reason, str)
    assert isinstance(score.is_first_occurrence, bool)
    assert isinstance(score.occurrence_count, int)
    assert isinstance(score.habituation_factor, float)
    assert 0.0 <= score.score <= 1.0
    assert 0.0 <= score.habituation_factor <= 1.0
