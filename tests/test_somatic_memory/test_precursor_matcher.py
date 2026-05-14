"""Tests for memory.somatic.precursor_matcher — Precursor learning, matching."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from memory.somatic.sensor_episode_store import SensorEpisode
from memory.somatic.precursor_matcher import PrecursorMatcher


def _make_episode(
    episode_id: str,
    signal_types: list[str],
    severity: float = 0.3,
    ts_offset_minutes: int = 0,
) -> SensorEpisode:
    ts = datetime.now(timezone.utc) - timedelta(minutes=ts_offset_minutes)
    return SensorEpisode(
        episode_id=episode_id,
        timestamp=ts,
        duration_ms=500.0,
        severity_peak=severity,
        signal_types=signal_types,
        environmental_signature={
            "cpu_band": "moderate",
            "memory_band": "light",
            "disk_band": "idle",
            "load_band": "light",
            "process_band": "normal",
            "composite_vector": [0.5, 0.35, 0.2, 0.2, 0.3],
        },
    )


def test_learn_precursors() -> None:
    """Learn precursor patterns from episode history."""
    matcher = PrecursorMatcher(severity_threshold=0.5, min_support=2)

    episodes = [
        _make_episode("pre-1a", ["mem_pressure"], severity=0.3, ts_offset_minutes=100),
        _make_episode("target-1", ["cpu_spike"], severity=0.9, ts_offset_minutes=85),
        _make_episode("pre-2a", ["mem_pressure"], severity=0.3, ts_offset_minutes=50),
        _make_episode("target-2", ["cpu_spike"], severity=0.85, ts_offset_minutes=35),
    ]

    patterns = matcher.learn_precursors(episodes, lookback_minutes=30)
    assert len(patterns) >= 1
    assert patterns[0].support_count >= 2
    assert patterns[0].confidence > 0


def test_match_current() -> None:
    """Detect precursor in current signals."""
    matcher = PrecursorMatcher(severity_threshold=0.5, min_support=2)

    episodes = [
        _make_episode("pre-a", ["mem_pressure"], severity=0.3, ts_offset_minutes=100),
        _make_episode("tgt-a", ["cpu_spike"], severity=0.8, ts_offset_minutes=85),
        _make_episode("pre-b", ["mem_pressure"], severity=0.35, ts_offset_minutes=50),
        _make_episode("tgt-b", ["cpu_spike"], severity=0.85, ts_offset_minutes=35),
    ]

    patterns = matcher.learn_precursors(episodes, lookback_minutes=30)

    current_signals = [{"type": "mem_pressure", "value": 0.4}]
    current_env = {
        "cpu_percent": 50.0,
        "memory_percent": 40.0,
        "disk_percent": 20.0,
        "load_1m": 1.0,
        "process_count": 150,
    }

    matches = matcher.match_current(current_signals, current_env, patterns)
    assert len(matches) >= 1
    assert matches[0].match_confidence > 0


def test_confidence_included() -> None:
    """All matches include a confidence score."""
    matcher = PrecursorMatcher(severity_threshold=0.5, min_support=2)

    episodes = [
        _make_episode("p1", ["io_wait"], severity=0.2, ts_offset_minutes=100),
        _make_episode("t1", ["disk_full"], severity=0.9, ts_offset_minutes=85),
        _make_episode("p2", ["io_wait"], severity=0.25, ts_offset_minutes=50),
        _make_episode("t2", ["disk_full"], severity=0.88, ts_offset_minutes=35),
    ]

    patterns = matcher.learn_precursors(episodes, lookback_minutes=30)
    current = [{"type": "io_wait", "value": 0.3}]
    env = {"cpu_percent": 30.0, "memory_percent": 30.0, "disk_percent": 70.0,
           "load_1m": 0.8, "process_count": 100}

    matches = matcher.match_current(current, env, patterns)
    for m in matches:
        assert 0.0 <= m.match_confidence <= 1.0
        assert m.recommended_action


def test_no_auto_action() -> None:
    """Matcher only reports — verify PrecursorMatch has recommended_action string, not a callable."""
    matcher = PrecursorMatcher()
    episodes = [
        _make_episode("p", ["x"], severity=0.2, ts_offset_minutes=100),
        _make_episode("t", ["y"], severity=0.8, ts_offset_minutes=85),
        _make_episode("p2", ["x"], severity=0.2, ts_offset_minutes=50),
        _make_episode("t2", ["y"], severity=0.9, ts_offset_minutes=35),
    ]

    patterns = matcher.learn_precursors(episodes, lookback_minutes=30)
    if patterns:
        matches = matcher.match_current(
            [{"type": "x", "value": 0.3}],
            {"cpu_percent": 40, "memory_percent": 40, "disk_percent": 20,
             "load_1m": 1.0, "process_count": 100},
            patterns,
        )
        for m in matches:
            assert isinstance(m.recommended_action, str)
            assert not callable(m.recommended_action)
