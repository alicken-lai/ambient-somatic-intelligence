"""Area 1: cognitive homeostasis orchestrator."""

from governance.metacognition.metacognitive_reflection import MetacognitiveVerdict


def test_evaluate_after_reflection_clean(cognitive_homeostasis) -> None:
    meta = MetacognitiveVerdict(
        reflective=True,
        quality_score=0.75,
        degradation_pressure=0.1,
        pathology_pressure=0.1,
    )
    v = cognitive_homeostasis.evaluate_after_reflection(
        meta,
        governed_salience=0.6,
        coherence_score=0.85,
        coherence_ok=True,
    )
    assert v.homeostasis_score >= 0.58
    assert v.stable is True


def test_stabilize_after_reflection_delegate(metacognitive_reflection) -> None:
    meta = metacognitive_reflection.evaluate_after_coherence(
        governed_salience=0.6,
        coherence_score=0.85,
    )
    homeo = metacognitive_reflection.stabilize_after_reflection(
        meta,
        governed_salience=0.6,
        coherence_score=0.85,
        coherence_ok=True,
    )
    assert homeo.homeostasis_score >= 0.0
