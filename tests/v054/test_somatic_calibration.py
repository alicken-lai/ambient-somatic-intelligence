"""Area 4: somatic calibration modules."""

from attention.calibration.confidence_cap import ABSOLUTE_MAX_CONFIDENCE
from attention.core.precursor_signal import PrecursorSignal
from attention.somatic.environmental_uncertainty import EnvironmentalUncertainty
from attention.somatic.precursor_reliability import PrecursorReliability
from attention.somatic.somatic_confidence import SomaticConfidenceCalibrator
from attention.somatic.somatic_episode import SomaticEpisode


def test_somatic_confidence_capped() -> None:
    ep = SomaticEpisode(severity_peak=0.95, environmental_signature={"a": 1, "b": 2})
    sc = SomaticConfidenceCalibrator().from_episode(ep)
    assert sc.calibrated <= ABSOLUTE_MAX_CONFIDENCE


def test_environmental_uncertainty_report() -> None:
    eu = EnvironmentalUncertainty()
    report = eu.report(count=2)
    assert report.mean_spread > 0


def test_precursor_reliability_capped() -> None:
    pr = PrecursorReliability()
    sig = PrecursorSignal(pattern_id="p1", strength=0.99, domain="telemetry")
    score = pr.score(sig)
    assert score.reliability <= ABSOLUTE_MAX_CONFIDENCE
