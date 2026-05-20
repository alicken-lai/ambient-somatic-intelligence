"""Area 2: somatic forecasting."""

from attention.somatic.environmental_risk_projection import EnvironmentalRiskProjector
from attention.somatic.precursor_resonance_forecast import PrecursorResonanceForecaster
from attention.somatic.somatic_episode import SomaticEpisode
from attention.somatic.somatic_forecast import SomaticForecast
from attention.core.precursor_signal import PrecursorSignal


def test_somatic_forecast() -> None:
    ep = SomaticEpisode(signal_types=["temp"], severity_peak=0.5, environmental_signature={"room": "a"})
    pt = SomaticForecast().forecast_episode(ep)
    assert 0.0 <= pt.resonance_projected <= 1.0


def test_environmental_risk() -> None:
    proj = EnvironmentalRiskProjector()
    ep = SomaticEpisode(signal_types=["hum"], severity_peak=0.4, environmental_signature={"zone": "b"})
    r = proj.project_from_episode(ep)
    assert r.risk_score <= 0.85


def test_precursor_resonance() -> None:
    ep = SomaticEpisode(signal_types=["vib"], severity_peak=0.5)
    sig = PrecursorSignal(pattern_id="p1", strength=0.6, domain="somatic")
    results = PrecursorResonanceForecaster().forecast(ep, [sig])
    assert isinstance(results, list)
