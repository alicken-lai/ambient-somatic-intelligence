"""Area 8: Observability v065c metrics."""

from observability.v065c.drift_decay_metrics import collect_drift_decay_metrics
from observability.v065c.precedence_guard_metrics import collect_precedence_guard_metrics
from observability.v065c.runtime_sandbox_metrics import collect_runtime_sandbox_metrics


def test_all_metrics_at_full_rate() -> None:
    assert collect_runtime_sandbox_metrics().containment_rate == 1.0
    assert collect_precedence_guard_metrics().guard_rate == 1.0
    assert collect_drift_decay_metrics().containment_rate == 1.0
