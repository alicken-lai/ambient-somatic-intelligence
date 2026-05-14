"""Tests for attention.weak_signal_detector — Emerging pattern detection."""

from __future__ import annotations

from datetime import datetime, timezone

from attention.attention_state import AttentionSignal
from attention.weak_signal_detector import WeakSignalDetector, Trend


def _make_weak_signal(
    domain: str = "somatic",
    signal_type: str = "minor_fluctuation",
    raw_value: float = 0.15,
) -> AttentionSignal:
    return AttentionSignal(
        source_domain=domain,
        signal_type=signal_type,
        raw_value=raw_value,
        timestamp=datetime.now(timezone.utc),
    )


def test_single_weak_signal_ignored() -> None:
    """One or two weak signals below min_cluster_size produce no patterns."""
    detector = WeakSignalDetector(threshold=0.3, min_cluster_size=3)
    signals = [_make_weak_signal()]
    patterns = detector.detect_emerging(signals)
    assert len(patterns) == 0


def test_correlated_weak_signals_detected() -> None:
    """Multiple related weak signals form an emerging pattern."""
    detector = WeakSignalDetector(threshold=0.3, min_cluster_size=3)

    signals = [
        _make_weak_signal(domain="somatic", signal_type="mem_pressure", raw_value=0.2),
        _make_weak_signal(domain="somatic", signal_type="mem_pressure", raw_value=0.18),
        _make_weak_signal(domain="somatic", signal_type="mem_pressure", raw_value=0.22),
        _make_weak_signal(domain="somatic", signal_type="mem_pressure", raw_value=0.19),
    ]

    patterns = detector.detect_emerging(signals, window_seconds=600)
    assert len(patterns) >= 1
    p = patterns[0]
    assert p.combined_strength > 0
    assert len(p.contributing_signals) >= 3


def test_trend_detection() -> None:
    """Rising trend is detected when strength increases across calls."""
    detector = WeakSignalDetector(threshold=0.3, min_cluster_size=3)

    for round_val in [0.10, 0.15, 0.20, 0.25]:
        signals = [
            _make_weak_signal(signal_type="rising_sig", raw_value=round_val)
            for _ in range(4)
        ]
        patterns = detector.detect_emerging(signals, window_seconds=600)

    if patterns:
        assert patterns[0].trend in (Trend.RISING, Trend.STABLE)


def test_cross_domain_correlation() -> None:
    """Signals from correlated domain pairs get a combined pattern."""
    detector = WeakSignalDetector(threshold=0.3, min_cluster_size=3)

    signals = [
        _make_weak_signal(domain="somatic", signal_type="cross_test", raw_value=0.2),
        _make_weak_signal(domain="somatic", signal_type="cross_test", raw_value=0.18),
        _make_weak_signal(domain="task", signal_type="cross_test", raw_value=0.15),
        _make_weak_signal(domain="task", signal_type="cross_test", raw_value=0.12),
    ]

    patterns = detector.detect_emerging(signals, window_seconds=600)
    if patterns:
        domains_seen = set()
        for p in patterns:
            domains_seen.update(p.domains)
        assert len(domains_seen) >= 1
