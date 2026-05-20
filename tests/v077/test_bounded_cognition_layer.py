"""Area 5: bounded cognition containment and decay."""

from governance.agency.bounded_cognition_containment import BoundedCognitionContainment
from governance.agency.cognition_decay_governor import CognitionDecayGovernor
from governance.agency.cognition_retention_boundary import CognitionRetentionBoundary


def test_bounded_cognition_containment() -> None:
    v = BoundedCognitionContainment().evaluate("unbounded cognition escalation")
    assert not v.bounded


def test_cognition_decay() -> None:
    v = CognitionDecayGovernor().govern(stale_hours=200.0)
    assert v.decay_applied


def test_cognition_retention_boundary() -> None:
    v = CognitionRetentionBoundary().bound(168.0)
    assert v.within_bounds
