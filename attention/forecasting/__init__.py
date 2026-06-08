"""attention.forecasting — bounded, probabilistic attention forecasting.

Projects salience, trajectories, precursor resolution, and pressure forward over
fixed windows.  Every forecast is a probabilistic projection, never a prediction,
and all uncertainty bands are bounded.
"""

from attention.forecasting.attention_forecast import (
    FORECAST_DISCLAIMER,
    AttentionForecast,
    AttentionForecastResult,
)
from attention.forecasting.forecast_uncertainty import ForecastUncertainty, UncertaintyBand
from attention.forecasting.forecast_window import (
    FORECAST_WINDOWS,
    MAX_HORIZON_SECONDS,
    ForecastWindow,
)
from attention.forecasting.precursor_forecast import (
    PrecursorForecast,
    PrecursorForecastPoint,
)
from attention.forecasting.replay_trajectory_forecast import (
    ReplayTrajectoryForecast,
    ReplayTrajectoryResult,
)
from attention.forecasting.salience_pressure_forecast import (
    PressureForecast,
    SaliencePressureForecast,
)
from attention.forecasting.salience_projection import (
    SalienceProjection,
    SalienceProjectionPoint,
)
from attention.forecasting.trajectory_estimator import (
    TrajectoryEstimate,
    TrajectoryEstimator,
)

__all__ = [
    "FORECAST_DISCLAIMER",
    "AttentionForecast",
    "AttentionForecastResult",
    "ForecastUncertainty",
    "UncertaintyBand",
    "FORECAST_WINDOWS",
    "MAX_HORIZON_SECONDS",
    "ForecastWindow",
    "PrecursorForecast",
    "PrecursorForecastPoint",
    "ReplayTrajectoryForecast",
    "ReplayTrajectoryResult",
    "PressureForecast",
    "SaliencePressureForecast",
    "SalienceProjection",
    "SalienceProjectionPoint",
    "TrajectoryEstimate",
    "TrajectoryEstimator",
]
