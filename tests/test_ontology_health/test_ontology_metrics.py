"""Tests for ontology health metrics."""

import pytest

from observability.ontology.ontology_metrics import MetricResult, OntologyMetrics


@pytest.fixture
def metrics():
    return OntologyMetrics()


# ── helpers ───────────────────────────────────────────────────────────────

def _assert_valid_metric(result: MetricResult) -> None:
    """Every metric result must be normalised to [0, 1]."""
    assert 0.0 <= result.value <= 1.0, (
        f"{result.name}: value {result.value} out of [0, 1]"
    )


# ── instinct_formation_rate ───────────────────────────────────────────────

class TestInstinctFormationRate:

    def test_in_healthy_range(self, metrics):
        result = metrics.measure_instinct_formation_rate(l1_count=100, l2_count=15)
        _assert_valid_metric(result)
        assert result.value == 1.0

    def test_at_low_boundary(self, metrics):
        result = metrics.measure_instinct_formation_rate(l1_count=100, l2_count=5)
        _assert_valid_metric(result)
        assert result.value == 1.0

    def test_at_high_boundary(self, metrics):
        result = metrics.measure_instinct_formation_rate(l1_count=100, l2_count=25)
        _assert_valid_metric(result)
        assert result.value == 1.0

    def test_too_low_rate(self, metrics):
        result = metrics.measure_instinct_formation_rate(l1_count=100, l2_count=1)
        _assert_valid_metric(result)
        assert result.value < 1.0

    def test_too_high_rate(self, metrics):
        result = metrics.measure_instinct_formation_rate(l1_count=100, l2_count=50)
        _assert_valid_metric(result)
        assert result.value < 1.0

    def test_zero_l1(self, metrics):
        result = metrics.measure_instinct_formation_rate(l1_count=0, l2_count=0)
        _assert_valid_metric(result)

    def test_name(self, metrics):
        result = metrics.measure_instinct_formation_rate(l1_count=10, l2_count=1)
        assert result.name == "instinct_formation_rate"


# ── promotion_precision ───────────────────────────────────────────────────

class TestPromotionPrecision:

    def test_all_successful(self, metrics):
        result = metrics.measure_promotion_precision(
            promoted_count=10, total_candidates=20, successful_promotions=10,
        )
        _assert_valid_metric(result)
        assert result.value == 1.0

    def test_none_successful(self, metrics):
        result = metrics.measure_promotion_precision(
            promoted_count=10, total_candidates=20, successful_promotions=0,
        )
        _assert_valid_metric(result)
        assert result.value == 0.0

    def test_half_successful(self, metrics):
        result = metrics.measure_promotion_precision(
            promoted_count=10, total_candidates=20, successful_promotions=5,
        )
        _assert_valid_metric(result)
        assert result.value == pytest.approx(0.5)

    def test_zero_promoted(self, metrics):
        result = metrics.measure_promotion_precision(
            promoted_count=0, total_candidates=10, successful_promotions=0,
        )
        _assert_valid_metric(result)
        assert result.value == 0.0


# ── decay_correctness ─────────────────────────────────────────────────────

class TestDecayCorrectness:

    def test_contradicted_lower(self, metrics):
        result = metrics.measure_decay_correctness(
            decayed_entries=[0.7, 0.6, 0.8],
            contradiction_entries=[0.2, 0.1, 0.3],
        )
        _assert_valid_metric(result)
        assert result.value == 1.0 or result.value > 0.7

    def test_contradicted_higher_is_bad(self, metrics):
        result = metrics.measure_decay_correctness(
            decayed_entries=[0.2, 0.1],
            contradiction_entries=[0.8, 0.9],
        )
        _assert_valid_metric(result)
        assert result.value == 0.0

    def test_no_contradiction_entries(self, metrics):
        result = metrics.measure_decay_correctness(
            decayed_entries=[0.5], contradiction_entries=[],
        )
        _assert_valid_metric(result)
        assert result.value == 1.0

    def test_no_decayed_entries(self, metrics):
        result = metrics.measure_decay_correctness(
            decayed_entries=[], contradiction_entries=[0.3],
        )
        _assert_valid_metric(result)


# ── verifier_integrity ────────────────────────────────────────────────────

class TestVerifierIntegrity:

    def test_all_self_certs_blocked(self, metrics):
        result = metrics.measure_verifier_integrity(
            total_verifications=10,
            self_certifications_blocked=3,
            independent_verifications=7,
        )
        _assert_valid_metric(result)
        assert result.value == 1.0

    def test_no_self_cert_attempts(self, metrics):
        result = metrics.measure_verifier_integrity(
            total_verifications=5,
            self_certifications_blocked=0,
            independent_verifications=5,
        )
        _assert_valid_metric(result)
        assert result.value == 1.0

    def test_some_leaked(self, metrics):
        result = metrics.measure_verifier_integrity(
            total_verifications=10,
            self_certifications_blocked=2,
            independent_verifications=5,
        )
        _assert_valid_metric(result)
        assert result.value < 1.0


# ── false_positive_resistance ─────────────────────────────────────────────

class TestFalsePositiveResistance:

    def test_no_false_promotions(self, metrics):
        result = metrics.measure_false_positive_resistance(
            noise_episodes=100, false_promotions=0,
        )
        _assert_valid_metric(result)
        assert result.value == 1.0

    def test_all_false_promotions(self, metrics):
        result = metrics.measure_false_positive_resistance(
            noise_episodes=10, false_promotions=10,
        )
        _assert_valid_metric(result)
        assert result.value == 0.0

    def test_zero_noise(self, metrics):
        result = metrics.measure_false_positive_resistance(
            noise_episodes=0, false_promotions=0,
        )
        _assert_valid_metric(result)
        assert result.value == 1.0


# ── strategic_emergence ───────────────────────────────────────────────────

class TestStrategicEmergence:

    def test_all_governed(self, metrics):
        result = metrics.measure_strategic_emergence(
            l3_count=10, l4_count=5, l4_with_governance=5,
        )
        _assert_valid_metric(result)
        assert result.value == 1.0

    def test_no_l4(self, metrics):
        result = metrics.measure_strategic_emergence(
            l3_count=10, l4_count=0, l4_with_governance=0,
        )
        _assert_valid_metric(result)
        assert result.value < 1.0

    def test_partial_governance(self, metrics):
        result = metrics.measure_strategic_emergence(
            l3_count=10, l4_count=4, l4_with_governance=2,
        )
        _assert_valid_metric(result)
        assert result.value < 1.0


# ── confidence_calibration ────────────────────────────────────────────────

class TestConfidenceCalibration:

    def test_all_correct(self, metrics):
        updates = [
            {"reason": "reuse_success", "delta": 0.05},
            {"reason": "reuse_failure", "delta": -0.1},
            {"reason": "contradiction", "delta": -0.15},
            {"reason": "decay", "delta": -0.02},
            {"reason": "validation", "delta": 0.01},
        ]
        result = metrics.measure_confidence_calibration(updates)
        _assert_valid_metric(result)
        assert result.value == 1.0

    def test_all_wrong(self, metrics):
        updates = [
            {"reason": "reuse_success", "delta": -0.1},
            {"reason": "reuse_failure", "delta": 0.05},
        ]
        result = metrics.measure_confidence_calibration(updates)
        _assert_valid_metric(result)
        assert result.value == 0.0

    def test_empty_updates(self, metrics):
        result = metrics.measure_confidence_calibration([])
        _assert_valid_metric(result)
        assert result.value == 1.0
