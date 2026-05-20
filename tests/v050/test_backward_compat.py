"""Area 10: backward compatibility with legacy attention/."""

from attention import (
    AttentionKernel,
    AttentionSignal,
    AttentionSnapshot,
    KernelSalienceEngine,
    PriorityAllocator,
    SalienceEngine,
)


def test_legacy_exports_still_available() -> None:
    assert SalienceEngine is not None
    assert PriorityAllocator is not None


def test_v050_exports_on_package() -> None:
    assert AttentionKernel is not None
    assert KernelSalienceEngine is not None


def test_legacy_engine_still_scores() -> None:
    engine = SalienceEngine()
    sig = AttentionSignal("somatic", "x", 0.9)
    score = engine.compute_salience(sig, AttentionSnapshot())
    assert score.total >= 0.45
