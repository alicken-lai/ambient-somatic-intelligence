"""Area 7: observability v060 metrics."""

from governance.cognition.salience_arbitrator import SalienceClaim
from observability.v060.arbitration_metrics import collect_arbitration_metrics
from observability.v060.uncertainty_override_metrics import collect_uncertainty_override_metrics


def test_arbitration_metrics() -> None:
    m = collect_arbitration_metrics([SalienceClaim("telemetry", 0.5, 0.8)])
    assert m.arbitration_count >= 1
    assert 0.0 <= m.mean_fairness <= 1.0


def test_uncertainty_metrics() -> None:
    m = collect_uncertainty_override_metrics([(0.7, 0.8)])
    assert m.mean_dampening_factor <= 1.0
