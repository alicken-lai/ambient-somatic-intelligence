"""Tests for memory.somatic.environmental_signature — Fingerprinting, distance, similarity."""

from __future__ import annotations

from memory.somatic.environmental_signature import EnvironmentalSignature


def test_from_snapshot() -> None:
    """Create a signature from raw metrics snapshot."""
    snapshot = {
        "cpu_percent": 55.0,
        "memory_percent": 42.0,
        "disk_percent": 30.0,
        "load_1m": 1.5,
        "process_count": 180,
    }
    sig = EnvironmentalSignature.from_snapshot(snapshot)

    assert sig.cpu_band == "moderate"
    assert sig.memory_band == "light"
    assert sig.disk_band == "idle"
    assert sig.process_band == "normal"
    assert len(sig.composite_vector) == 5
    assert all(0.0 <= v <= 1.0 for v in sig.composite_vector)


def test_fingerprint_deterministic() -> None:
    """Same input produces the same fingerprint hash."""
    sig1 = EnvironmentalSignature(
        cpu_band="heavy",
        memory_band="moderate",
        disk_band="idle",
        load_band="light",
        process_band="normal",
    )
    sig2 = EnvironmentalSignature(
        cpu_band="heavy",
        memory_band="moderate",
        disk_band="idle",
        load_band="light",
        process_band="normal",
    )

    assert sig1.fingerprint() == sig2.fingerprint()
    assert len(sig1.fingerprint()) == 64  # SHA-256 hex


def test_distance_identical() -> None:
    """Distance to self is 0.0."""
    sig = EnvironmentalSignature(
        composite_vector=[0.5, 0.3, 0.2, 0.4, 0.6]
    )
    assert sig.distance_to(sig) == 0.0


def test_distance_different() -> None:
    """Dissimilar environments have high distance."""
    idle = EnvironmentalSignature(
        composite_vector=[0.05, 0.1, 0.05, 0.05, 0.1]
    )
    saturated = EnvironmentalSignature(
        composite_vector=[0.95, 0.9, 0.85, 0.9, 0.8]
    )

    dist = idle.distance_to(saturated)
    assert dist > 0.5


def test_similarity_threshold() -> None:
    """is_similar_to works with threshold parameter."""
    sig_a = EnvironmentalSignature(
        composite_vector=[0.5, 0.5, 0.5, 0.5, 0.5]
    )
    sig_b = EnvironmentalSignature(
        composite_vector=[0.52, 0.48, 0.51, 0.49, 0.50]
    )
    sig_c = EnvironmentalSignature(
        composite_vector=[0.1, 0.9, 0.1, 0.9, 0.1]
    )

    assert sig_a.is_similar_to(sig_b, threshold=0.15) is True
    assert sig_a.is_similar_to(sig_c, threshold=0.15) is False


def test_serialization_roundtrip() -> None:
    """to_dict / from_dict preserves all fields."""
    original = EnvironmentalSignature(
        cpu_band="heavy",
        memory_band="moderate",
        disk_band="light",
        load_band="heavy",
        process_band="high",
        composite_vector=[0.8, 0.6, 0.5, 0.7, 0.65],
    )

    d = original.to_dict()
    restored = EnvironmentalSignature.from_dict(d)

    assert restored.cpu_band == original.cpu_band
    assert restored.memory_band == original.memory_band
    assert restored.process_band == original.process_band
    assert len(restored.composite_vector) == 5
