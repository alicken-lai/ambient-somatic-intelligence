"""Area 2: cognition quality scoring."""

from governance.metacognition.cognition_quality import CognitionQuality


def test_quality_floor_clean() -> None:
    cq = CognitionQuality()
    s = cq.score(
        governed_salience=0.6,
        coherence_score=0.9,
        constitutional_compliant=True,
        identity_trusted=True,
        accepted=True,
    )
    assert s >= cq.QUALITY_FLOOR


def test_quality_reduced_when_not_accepted() -> None:
    cq = CognitionQuality()
    clean = cq.score(
        governed_salience=0.6,
        coherence_score=0.9,
        accepted=True,
    )
    rejected = cq.score(
        governed_salience=0.6,
        coherence_score=0.9,
        accepted=False,
    )
    assert rejected < clean
