"""Area 2: Phase 1 temporal continuity core."""

from governance.temporal.continuity_record import ContinuityRecord
from governance.temporal.epoch_identity import EpochIdentity
from governance.temporal.temporal_boundary import TemporalBoundary
from governance.temporal.temporal_continuity import TemporalContinuity


def test_temporal_boundary_blocks_immortal() -> None:
    tb = TemporalBoundary()
    v = tb.evaluate("Enable immortal cognition across all epochs.")
    assert not v.boundary_safe
    assert "immortal_cognition" in v.violations


def test_epoch_identity_stable() -> None:
    v = EpochIdentity().resolve("Advisory epoch with labeled parent.")
    assert v.identity_stable


def test_temporal_continuity_clean() -> None:
    v = TemporalContinuity().evaluate("Advisory bounded epoch continuity.")
    assert v.continuous
    assert v.advisory_only is True


def test_continuity_record_bounded() -> None:
    rec = ContinuityRecord.create(
        epoch_id="e1",
        runtime_id="ambient",
        summary="probe",
        retention_hours=168.0,
    )
    assert rec.record_id
    assert rec.to_dict()["advisory_only"] is True
