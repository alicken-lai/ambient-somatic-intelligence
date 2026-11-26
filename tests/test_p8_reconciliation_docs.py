"""P8 reconciliation text keeps historical claims from being reread as a new release."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_p8_reconciliation_records_unmet_gates_without_a_new_release() -> None:
    text = (ROOT / "docs" / "release" / "P8_DOCUMENTATION_RECONCILIATION_2026-11-20.md").read_text(encoding="utf-8")
    for token in (
        "P8_RELEASE_TAG：** NOT_REQUESTED",
        "P4_INDEPENDENT_VERDICT：** NOT_REISSUED",
        "P7_COMPLETION：** NOT_MET",
        "P1_GATES：** DEFERRED_OPTION_A",
        "P5_STATUS：** EXISTING_GATE_REVERIFIED",
        "P6_STATUS：** NOT_PROMOTED",
        "does not claim AGI, autonomy, or unconstrained production",
    ):
        assert token in text
    assert "APPROVED_FOR_TAGGING" not in text


def test_review_packet_does_not_issue_an_implementer_verdict() -> None:
    text = (ROOT / "docs" / "p7" / "P7_INDEPENDENT_REVIEW_PACKET_2026-11-20.md").read_text(encoding="utf-8")
    assert "REVIEW_STATUS：** AWAITING_INDEPENDENT_REVIEWER" in text
    assert "IMPLEMENTER_VERDICT：** NONE" in text
    assert "pilot_acceptance：** not_claimed" in text
