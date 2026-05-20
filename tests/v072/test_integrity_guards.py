"""Area 6: Phase 5 integrity guards."""

from governance.temporal.continuity_contamination_guard import ContinuityContaminationGuard
from governance.temporal.false_lineage_detector import FalseLineageDetector
from governance.temporal.temporal_integrity_monitor import TemporalIntegrityMonitor


def test_contamination_guard() -> None:
    g = ContinuityContaminationGuard()
    assert not g.scan("Label epoch claims.").contaminated
    assert g.scan("False continuity inheritance from foreign epoch.").contaminated


def test_false_lineage_detector() -> None:
    det = FalseLineageDetector()
    assert not det.scan("Labeled parent epoch.").false_lineage
    assert det.scan("Permanent federation memory for all epochs.").false_lineage


def test_integrity_monitor() -> None:
    mon = TemporalIntegrityMonitor()
    assert mon.check("Advisory temporal continuity.").integrity_ok
    assert not mon.check("Weaken Guardian and rewrite history.").integrity_ok
