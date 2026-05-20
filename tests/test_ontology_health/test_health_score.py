"""Tests for the Ontology Health Score system."""

import pytest

from observability.ontology.ontology_health_score import (
    HealthClassification,
    HealthReport,
    OntologyHealthScore,
)


@pytest.fixture
def scorer():
    return OntologyHealthScore(threshold=0.85)


# ── Weight sanity ─────────────────────────────────────────────────────────

def test_weights_sum_to_one():
    total = sum(OntologyHealthScore.METRIC_WEIGHTS.values())
    assert total == pytest.approx(1.0)


# ── Classification thresholds ─────────────────────────────────────────────

class TestClassify:

    def test_stable(self, scorer):
        assert scorer.classify(0.95) == HealthClassification.STABLE
        assert scorer.classify(0.90) == HealthClassification.STABLE

    def test_usable(self, scorer):
        assert scorer.classify(0.80) == HealthClassification.USABLE
        assert scorer.classify(0.75) == HealthClassification.USABLE

    def test_experimental(self, scorer):
        assert scorer.classify(0.60) == HealthClassification.EXPERIMENTAL
        assert scorer.classify(0.50) == HealthClassification.EXPERIMENTAL

    def test_unstable(self, scorer):
        assert scorer.classify(0.49) == HealthClassification.UNSTABLE
        assert scorer.classify(0.0) == HealthClassification.UNSTABLE


# ── Release gate ──────────────────────────────────────────────────────────

class TestReleasegate:

    def test_passes_above_threshold(self, scorer):
        report = HealthReport(
            score=0.90,
            classification=HealthClassification.STABLE,
            metrics=[],
            timestamp=None,
            details="",
            passing=True,
            threshold=0.85,
        )
        assert scorer.passes_release_gate(report) is True

    def test_fails_below_threshold(self, scorer):
        report = HealthReport(
            score=0.70,
            classification=HealthClassification.USABLE,
            metrics=[],
            timestamp=None,
            details="",
            passing=False,
            threshold=0.85,
        )
        assert scorer.passes_release_gate(report) is False

    def test_exact_threshold(self, scorer):
        report = HealthReport(
            score=0.85,
            classification=HealthClassification.USABLE,
            metrics=[],
            timestamp=None,
            details="",
            passing=True,
            threshold=0.85,
        )
        assert scorer.passes_release_gate(report) is True


# ── compute ───────────────────────────────────────────────────────────────

def _perfect_inputs() -> dict:
    return {
        "instinct_formation_rate": {"l1_count": 100, "l2_count": 15},
        "promotion_precision": {
            "promoted_count": 10,
            "total_candidates": 20,
            "successful_promotions": 10,
        },
        "decay_correctness": {
            "decayed_entries": [0.7, 0.6, 0.8],
            "contradiction_entries": [0.2, 0.1, 0.3],
        },
        "verifier_integrity": {
            "total_verifications": 10,
            "self_certifications_blocked": 3,
            "independent_verifications": 7,
        },
        "false_positive_resistance": {
            "noise_episodes": 50,
            "false_promotions": 0,
        },
        "strategic_emergence": {
            "l3_count": 10,
            "l4_count": 5,
            "l4_with_governance": 5,
        },
        "confidence_calibration": {
            "confidence_updates": [
                {"reason": "reuse_success", "delta": 0.05},
                {"reason": "reuse_failure", "delta": -0.1},
                {"reason": "decay", "delta": -0.02},
            ],
        },
    }


def _worst_inputs() -> dict:
    return {
        "instinct_formation_rate": {"l1_count": 100, "l2_count": 100},
        "promotion_precision": {
            "promoted_count": 10,
            "total_candidates": 20,
            "successful_promotions": 0,
        },
        "decay_correctness": {
            "decayed_entries": [0.1, 0.2],
            "contradiction_entries": [0.9, 0.8],
        },
        "verifier_integrity": {
            "total_verifications": 10,
            "self_certifications_blocked": 0,
            "independent_verifications": 0,
        },
        "false_positive_resistance": {
            "noise_episodes": 10,
            "false_promotions": 10,
        },
        "strategic_emergence": {
            "l3_count": 0,
            "l4_count": 0,
            "l4_with_governance": 0,
        },
        "confidence_calibration": {
            "confidence_updates": [
                {"reason": "reuse_success", "delta": -0.1},
                {"reason": "reuse_failure", "delta": 0.05},
            ],
        },
    }


class TestCompute:

    def test_produces_valid_report(self, scorer):
        report = scorer.compute(**_perfect_inputs())
        assert isinstance(report, HealthReport)
        assert 0.0 <= report.score <= 1.0
        assert isinstance(report.classification, HealthClassification)
        assert len(report.metrics) == 7

    def test_perfect_inputs_give_stable(self, scorer):
        report = scorer.compute(**_perfect_inputs())
        assert report.classification == HealthClassification.STABLE
        assert report.passing is True

    def test_worst_inputs_give_unstable(self, scorer):
        report = scorer.compute(**_worst_inputs())
        assert report.classification == HealthClassification.UNSTABLE
        assert report.passing is False

    def test_no_inputs_gives_zero(self, scorer):
        report = scorer.compute()
        assert report.score == pytest.approx(0.0)
        assert report.classification == HealthClassification.UNSTABLE

    def test_metric_weights_applied(self, scorer):
        report = scorer.compute(**_perfect_inputs())
        for m in report.metrics:
            assert m.weight > 0.0


class TestComputeFromTestResults:

    def test_flat_keys_work(self, scorer):
        tr = {
            "l1_count": 100,
            "l2_count": 15,
            "promoted_count": 10,
            "total_candidates": 20,
            "successful_promotions": 10,
            "decayed_entries": [0.7, 0.6],
            "contradiction_entries": [0.2, 0.1],
            "total_verifications": 10,
            "self_certs_blocked": 3,
            "independent_verifications": 7,
            "noise_episodes": 50,
            "false_promotions": 0,
            "l3_count": 10,
            "l4_count": 5,
            "l4_with_governance": 5,
            "confidence_updates": [
                {"reason": "reuse_success", "delta": 0.05},
            ],
        }
        report = scorer.compute_from_test_results(tr)
        assert isinstance(report, HealthReport)
        assert report.score > 0.0


# ── Report generation ─────────────────────────────────────────────────────

class TestGenerateReport:

    def test_report_is_markdown(self, scorer):
        report = scorer.compute(**_perfect_inputs())
        text = scorer.generate_report(report)
        assert "# Ontology Health Report" in text
        assert "Score:" in text
        assert "Classification:" in text

    def test_report_in_details(self, scorer):
        report = scorer.compute(**_perfect_inputs())
        assert "# Ontology Health Report" in report.details
