"""Area 8: observability v065 metrics."""

from observability.v065.calibration_recovery_metrics import collect_calibration_recovery_metrics
from observability.v065.coherence_recovery_metrics import collect_coherence_recovery_metrics
from observability.v065.reflection_balance_metrics import collect_reflection_balance_metrics
from observability.v065.salience_damping_metrics import collect_salience_damping_metrics
from observability.v065.stabilization_metrics import collect_stabilization_metrics


def test_all_metrics_collect() -> None:
    assert collect_stabilization_metrics().containment_rate >= 0.0
    assert collect_salience_damping_metrics().containment_rate >= 0.0
    assert collect_coherence_recovery_metrics().recovery_ready_rate >= 0.0
    assert collect_reflection_balance_metrics().balance_rate >= 0.0
    assert collect_calibration_recovery_metrics().bounded_rate >= 0.0
