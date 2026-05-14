"""Tests for memory.somatic.anomaly_fingerprint — Fingerprint creation, matching."""

from __future__ import annotations

from memory.somatic.anomaly_fingerprint import AnomalyFingerprint
from memory.somatic.environmental_signature import EnvironmentalSignature


def _make_env(cpu: str = "heavy") -> EnvironmentalSignature:
    return EnvironmentalSignature(
        cpu_band=cpu,
        memory_band="moderate",
        disk_band="idle",
        load_band="moderate",
        process_band="normal",
        composite_vector=[0.7, 0.5, 0.3, 0.4, 0.3],
    )


def test_create_fingerprint() -> None:
    """Create a fingerprint from a signals list."""
    signals = [
        {"type": "cpu_spike", "value": 0.8, "timestamp": 1700000000.0},
        {"type": "memory_pressure", "value": 0.6, "timestamp": 1700000001.0},
    ]
    env = _make_env()
    fp = AnomalyFingerprint.from_signals(signals, env)

    assert fp.fingerprint_id
    assert len(fp.fingerprint_id) == 24
    assert fp.signal_pattern  # non-empty
    assert "CPU_SPIKE" in fp.signal_pattern
    assert "MEMORY_PRESSURE" in fp.signal_pattern
    assert fp.severity_band in ("low", "medium", "high", "critical")
    assert fp.occurrence_count == 1


def test_fingerprint_match_identical() -> None:
    """Same anomaly pattern matches with high score."""
    signals = [
        {"type": "cpu_spike", "value": 0.8, "timestamp": 1700000000.0},
    ]
    env = _make_env()

    fp1 = AnomalyFingerprint.from_signals(signals, env)
    fp2 = AnomalyFingerprint.from_signals(signals, env)

    score = fp1.match(fp2)
    assert score >= 0.8


def test_fingerprint_match_different() -> None:
    """Different anomaly patterns have low match score."""
    signals_a = [
        {"type": "cpu_spike", "value": 0.9, "timestamp": 1700000000.0},
    ]
    signals_b = [
        {"type": "disk_io", "value": 0.3, "timestamp": 1700000000.0},
    ]

    fp_a = AnomalyFingerprint.from_signals(signals_a, _make_env("heavy"))
    fp_b = AnomalyFingerprint.from_signals(signals_b, _make_env("idle"))

    score = fp_a.match(fp_b)
    assert score < 0.6


def test_fingerprint_serialization() -> None:
    """to_dict / from_dict roundtrip preserves fields."""
    signals = [
        {"type": "cpu_spike", "value": 0.75, "timestamp": 1700000000.0},
    ]
    original = AnomalyFingerprint.from_signals(signals, _make_env())

    d = original.to_dict()
    restored = AnomalyFingerprint.from_dict(d)

    assert restored.fingerprint_id == original.fingerprint_id
    assert restored.signal_pattern == original.signal_pattern
    assert restored.severity_band == original.severity_band
    assert restored.temporal_pattern == original.temporal_pattern
