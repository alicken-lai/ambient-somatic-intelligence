"""P6 keeps the historical reality miss unpromoted."""

from __future__ import annotations

import pytest

from hermes.reality_debt import (
    HISTORICAL_CONTINUITY,
    HISTORICAL_PRECURSOR,
    NOT_PROMOTED,
    READY_FOR_INDEPENDENT_REVIEW,
    assess_reality_debt,
    external_untrusted,
    historical_reality_debt,
    refuse_bootstrap_relabel,
)


def test_historical_scores_stay_not_promoted() -> None:
    assessment = historical_reality_debt()
    assert assessment.continuity == HISTORICAL_CONTINUITY
    assert assessment.precursor == HISTORICAL_PRECURSOR
    assert assessment.status == NOT_PROMOTED
    assert assessment.promoted is False
    assert assessment.multi_incident_validation == "UNPROVEN"


def test_thresholds_cannot_be_lowered_to_clear_the_historical_miss() -> None:
    with pytest.raises(ValueError):
        assess_reality_debt(HISTORICAL_CONTINUITY, HISTORICAL_PRECURSOR, continuity_threshold=0.77)
    with pytest.raises(ValueError):
        refuse_bootstrap_relabel(NOT_PROMOTED, "BOOTSTRAP_GAP")


def test_meeting_thresholds_still_requires_an_independent_reviewer() -> None:
    assessment = assess_reality_debt(0.96, 0.61)
    assert assessment.status == READY_FOR_INDEPENDENT_REVIEW
    assert assessment.promoted is False


def test_external_observation_cannot_enter_dmn_or_guardian_policy() -> None:
    wrapped = external_untrusted({"source": "outside", "value": "unverified"})
    assert wrapped["trust"] == "external_untrusted"
    assert wrapped["may_enter_dmn_truth"] is False
    assert wrapped["may_change_guardian_policy"] is False
