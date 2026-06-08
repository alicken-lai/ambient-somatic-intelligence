"""Unit tests for the attention.forecasting package + forecast explainability."""

from __future__ import annotations

from attention.consolidation.precursor_memory import PrecursorMemory
from attention.consolidation.salience_history import SalienceHistory
from attention.core.attention_target import AttentionTarget
from attention.core.precursor_signal import PrecursorSignal
from attention.explainability.forecast_explainer import ForecastExplainer
from attention.explainability.precursor_chain_explainer import PrecursorChainExplainer
from attention.explainability.uncertainty_explainer import UncertaintyExplainer
from attention.forecasting.attention_forecast import AttentionForecast, FORECAST_DISCLAIMER
from attention.forecasting.forecast_uncertainty import ForecastUncertainty, UncertaintyBand
from attention.forecasting.forecast_window import FORECAST_WINDOWS, MAX_HORIZON_SECONDS
from attention.forecasting.precursor_forecast import PrecursorForecast
from attention.forecasting.replay_trajectory_forecast import ReplayTrajectoryForecast
from attention.forecasting.salience_projection import SalienceProjection
from attention.forecasting.trajectory_estimator import TrajectoryEstimator


def _forecaster() -> AttentionForecast:
    return AttentionForecast()


# --- windows + uncertainty ---------------------------------------------------

def test_forecast_windows_bounded() -> None:
    assert set(FORECAST_WINDOWS.keys()) == {"6h", "24h", "7d", "30d"}
    assert FORECAST_WINDOWS["30d"].horizon_seconds <= MAX_HORIZON_SECONDS


def test_uncertainty_band_bounded_and_capped() -> None:
    band = ForecastUncertainty().band(0.5, horizon_factor=2.0, sample_count=5)
    assert 0.0 <= band.low <= band.mid <= band.high <= 1.0
    wide = ForecastUncertainty(max_spread=0.35).band(0.8, horizon_factor=10.0, sample_count=20)
    assert wide.width() <= 0.35


# --- projection + trajectory -------------------------------------------------

def test_salience_projection_steps() -> None:
    hist = SalienceHistory()
    hist.record("t1", 0.4)
    pts = SalienceProjection(hist).project("t1", steps=5)
    assert len(pts) == 5
    assert all(0.0 <= p.projected_salience <= 1.0 for p in pts)
    assert SalienceProjection(hist).project("unknown", steps=5) == []


def test_trajectory_direction() -> None:
    rising = TrajectoryEstimator().estimate([0.2, 0.4, 0.6])
    assert rising.direction == "rising"
    falling = TrajectoryEstimator().estimate([0.7, 0.5, 0.3])
    assert falling.direction == "falling"
    empty = TrajectoryEstimator().estimate([])
    assert empty.direction == "stable"
    assert empty.sample_count == 0


# --- precursor forecast ------------------------------------------------------

def test_precursor_forecast_matched() -> None:
    mem = PrecursorMemory()
    sig = PrecursorSignal(pattern_id="pat-a", strength=0.7, domain="telemetry")
    mem.remember(sig)
    pt = PrecursorForecast(mem).forecast_from_signal(sig)
    assert pt is not None
    assert pt.likelihood > 0.0


def test_precursor_forecast_unknown_memory_returns_none() -> None:
    mem = PrecursorMemory()
    sig = PrecursorSignal(pattern_id="never-seen", strength=0.5, domain="telemetry")
    assert PrecursorForecast(mem).forecast_from_signal(sig) is None


def test_precursor_forecast_no_memory_produces_point() -> None:
    sig = PrecursorSignal(pattern_id="x", strength=0.5, domain="somatic")
    points = PrecursorForecast().forecast_batch([sig])
    assert len(points) == 1


# --- replay + unified forecast ----------------------------------------------

def test_replay_trajectory() -> None:
    hist = SalienceHistory()
    for v in (0.4, 0.5, 0.55):
        hist.record("t-replay", v)
    result = ReplayTrajectoryForecast(hist).forecast("t-replay", FORECAST_WINDOWS["6h"])
    assert result.replay_depth == 3
    assert len(result.estimates) == 1


def test_unified_forecast() -> None:
    fc = _forecaster()
    t = AttentionTarget(source_domain="telemetry", signal_type="fc", raw_value=0.55)
    fc.ingest(t)
    result = fc.forecast(t.target_id, "24h")
    assert result.disclaimer == FORECAST_DISCLAIMER
    assert result.trajectory is not None
    assert result.pressure is not None
    assert 0.0 <= result.pressure.projected_pressure <= 1.0


def test_forecast_all_windows() -> None:
    fc = _forecaster()
    t = AttentionTarget(source_domain="somatic", signal_type="w", raw_value=0.4)
    fc.ingest(t)
    all_r = fc.forecast_all_windows(t.target_id)
    assert set(all_r.keys()) == {"6h", "24h", "7d", "30d"}


# --- forecast explainability -------------------------------------------------

def test_uncertainty_explainer_probabilistic() -> None:
    band = UncertaintyBand(0.3, 0.5, 0.7, confidence=0.8)
    exp = UncertaintyExplainer().explain_band(band)
    assert "probabilistic" in exp["interpretation"].lower()


def test_forecast_explainer_disclaimer() -> None:
    fc = _forecaster()
    t = AttentionTarget(source_domain="telemetry", signal_type="ex", raw_value=0.5)
    fc.ingest(t)
    result = fc.forecast(t.target_id)
    exp = ForecastExplainer().explain(result)
    assert "probabilistic" in exp["summary"].lower()
    assert exp["disclaimer"] == result.disclaimer


def test_precursor_chain_explainer_empty() -> None:
    exp = PrecursorChainExplainer().explain_chain([])
    assert exp["chain_length"] == 0
