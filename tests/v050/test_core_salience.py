"""Area 1: core 10-dimension salience."""

from attention.core.salience import SalienceVector, compute_weighted_salience
from attention.core.salience_factor import ALL_DIMENSIONS, DEFAULT_DIMENSION_WEIGHTS


def test_ten_dimensions_present() -> None:
    assert len(ALL_DIMENSIONS) == 10
    assert abs(sum(DEFAULT_DIMENSION_WEIGHTS.values()) - 1.0) < 0.01


def test_weighted_salience_clamped() -> None:
    dims = {d: 1.0 for d in ALL_DIMENSIONS}
    assert compute_weighted_salience(dims) >= 0.99


def test_vector_total_matches_compute() -> None:
    v = SalienceVector("t1", {d: 0.5 for d in ALL_DIMENSIONS})
    assert v.total == compute_weighted_salience(v.dimensions, v.weights)
