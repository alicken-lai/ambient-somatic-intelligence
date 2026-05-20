"""Area 4: replay trajectory forecast."""

from attention.forecasting.forecast_window import FORECAST_WINDOWS
from attention.forecasting.replay_trajectory_forecast import ReplayTrajectoryForecast
from attention.consolidation.salience_history import SalienceHistory


def test_replay_forecast() -> None:
    hist = SalienceHistory()
    hist.record("t-replay", 0.4)
    hist.record("t-replay", 0.5)
    hist.record("t-replay", 0.55)
    rf = ReplayTrajectoryForecast(hist)
    result = rf.forecast("t-replay", FORECAST_WINDOWS["6h"])
    assert result.replay_depth > 0
    assert len(result.estimates) == 1
