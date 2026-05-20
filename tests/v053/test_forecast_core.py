"""Area 1: forecasting core modules."""

from attention.forecasting.forecast_window import FORECAST_WINDOWS, MAX_HORIZON_SECONDS
from attention.forecasting.forecast_uncertainty import ForecastUncertainty
from attention.forecasting.salience_projection import SalienceProjection


def test_forecast_windows() -> None:
    assert set(FORECAST_WINDOWS.keys()) == {"6h", "24h", "7d", "30d"}
    assert FORECAST_WINDOWS["30d"].horizon_seconds <= MAX_HORIZON_SECONDS


def test_uncertainty_band_bounded() -> None:
    band = ForecastUncertainty().band(0.5, horizon_factor=2.0, sample_count=5)
    assert 0.0 <= band.low <= band.mid <= band.high <= 1.0


def test_salience_projection(forecaster) -> None:
    from attention.core.attention_target import AttentionTarget

    t = AttentionTarget(source_domain="telemetry", signal_type="t1", raw_value=0.6)
    forecaster.ingest(t)
    pts = forecaster.projection.project(t.target_id, steps=5)
    assert len(pts) == 5
