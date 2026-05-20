"""Area 3: uncertainty bands."""

from attention.explainability.uncertainty_explainer import UncertaintyExplainer
from attention.forecasting.forecast_uncertainty import ForecastUncertainty, UncertaintyBand


def test_band_width_cap() -> None:
    m = ForecastUncertainty(max_spread=0.35)
    band = m.band(0.8, horizon_factor=10.0, sample_count=20)
    assert band.width() <= 0.35


def test_uncertainty_explainer() -> None:
    band = UncertaintyBand(0.3, 0.5, 0.7, confidence=0.8)
    exp = UncertaintyExplainer().explain_band(band)
    assert "probabilistic" in exp["interpretation"].lower()
