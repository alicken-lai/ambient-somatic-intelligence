"""Area 2: Phase 1 reality alignment core."""

from governance.reality.operational_truth_record import OperationalTruthRecord
from governance.reality.reality_alignment import RealityAlignment
from governance.reality.reality_boundary import RealityBoundary
from governance.reality.reality_exchange import RealityExchange


def test_reality_boundary_blocks_merge() -> None:
    rb = RealityBoundary()
    v = rb.evaluate("Merge sovereign realities into one canonical truth.")
    assert not v.boundary_safe
    assert "merge_sovereign_realities" in v.violations


def test_reality_exchange_compare_only() -> None:
    left = OperationalTruthRecord("l", "ambient", "ops stable")
    right = OperationalTruthRecord("r", "foreign", "ops advisory")
    ex = RealityExchange().compare(left, right)
    assert ex.divergence is not None
    assert ex.divergence.merge_forbidden is True


def test_reality_alignment_clean() -> None:
    v = RealityAlignment().evaluate("Advisory bounded cross-runtime alignment.")
    assert v.aligned
    assert v.advisory_only is True
