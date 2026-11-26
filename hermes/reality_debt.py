"""P6 reality-debt gate.

Historical misses stay NOT_PROMOTED. Thresholds cannot be lowered, and a debt
record cannot be relabeled as BOOTSTRAP_GAP. This module does not issue PASS.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CONTINUITY_THRESHOLD = 0.95
PRECURSOR_THRESHOLD = 0.60
HISTORICAL_CONTINUITY = 0.7712
HISTORICAL_PRECURSOR = 0.56
NOT_PROMOTED = "NOT_PROMOTED"
READY_FOR_INDEPENDENT_REVIEW = "READY_FOR_INDEPENDENT_REVIEW"


@dataclass(frozen=True)
class RealityDebtAssessment:
    status: str
    continuity: float
    precursor: float
    continuity_threshold: float
    precursor_threshold: float
    multi_incident_validation: str = "UNPROVEN"

    @property
    def promoted(self) -> bool:
        return False


def assess_reality_debt(
    continuity: float,
    precursor: float,
    *,
    continuity_threshold: float = CONTINUITY_THRESHOLD,
    precursor_threshold: float = PRECURSOR_THRESHOLD,
) -> RealityDebtAssessment:
    if continuity_threshold < CONTINUITY_THRESHOLD or precursor_threshold < PRECURSOR_THRESHOLD:
        raise ValueError("reality thresholds cannot be lowered")
    below = continuity < continuity_threshold or precursor < precursor_threshold
    status = NOT_PROMOTED if below else READY_FOR_INDEPENDENT_REVIEW
    return RealityDebtAssessment(
        status=status,
        continuity=continuity,
        precursor=precursor,
        continuity_threshold=continuity_threshold,
        precursor_threshold=precursor_threshold,
    )


def historical_reality_debt() -> RealityDebtAssessment:
    """Return the retained 2026-09 historical miss. The numbers are not rewritten."""

    return assess_reality_debt(HISTORICAL_CONTINUITY, HISTORICAL_PRECURSOR)


def refuse_bootstrap_relabel(current_label: str, proposed_label: str) -> str:
    if current_label == NOT_PROMOTED and proposed_label == "BOOTSTRAP_GAP":
        raise ValueError("historical reality debt cannot be relabeled as BOOTSTRAP_GAP")
    return current_label


def external_untrusted(record: dict[str, Any]) -> dict[str, Any]:
    """External observations stay untrusted and cannot become DMN truth or Guardian policy."""

    return {
        **record,
        "trust": "external_untrusted",
        "may_enter_dmn_truth": False,
        "may_change_guardian_policy": False,
    }
