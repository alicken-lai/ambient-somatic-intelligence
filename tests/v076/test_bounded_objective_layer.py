"""Area 5: Bounded objective containment and decay."""

from governance.purpose.bounded_objective_containment import BoundedObjectiveContainment
from governance.purpose.motivational_retention_boundary import MotivationalRetentionBoundary
from governance.purpose.optimization_decay_governor import OptimizationDecayGovernor


def test_bounded_objective_containment() -> None:
    v = BoundedObjectiveContainment().evaluate("Advisory bounded optimization.")
    assert v.bounded


def test_optimization_decay_governor() -> None:
    v = OptimizationDecayGovernor().govern(stale_hours=336)
    assert 0 < v.decay_factor < 1.0


def test_retention_boundary_caps() -> None:
    v = MotivationalRetentionBoundary().bound(20000.0)
    assert v.capped_hours <= 8760.0
