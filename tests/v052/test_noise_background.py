"""Area 4: noise classifier and benign patterns."""

from attention.consolidation.background_stability import BackgroundStability
from attention.consolidation.benign_pattern_memory import BenignPatternMemory
from attention.consolidation.noise_classifier import NoiseClassifier
from attention.consolidation.attention_trace import AttentionTrace


def test_noise_repeat_classification() -> None:
    nc = NoiseClassifier()
    for _ in range(5):
        r = nc.observe("telemetry", "heartbeat", 0.05)
    assert r.is_noise is True


def test_benign_memory_cap() -> None:
    b = BenignPatternMemory(max_patterns=2)
    b.record("a", "x")
    b.record("b", "y")
    b.record("c", "z")
    assert b.count <= 2


def test_background_stability_score() -> None:
    trace = AttentionTrace()
    benign = BenignPatternMemory()
    score = BackgroundStability().score(trace, benign)
    assert 0.0 <= score <= 1.0
