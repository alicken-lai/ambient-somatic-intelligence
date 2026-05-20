"""Area 6: Phase 5 integrity guards."""

from governance.reality.reality_contamination_guard import RealityContaminationGuard
from governance.reality.reality_integrity_monitor import RealityIntegrityMonitor
from governance.reality.truth_override_detector import TruthOverrideDetector


def test_contamination_guard() -> None:
    g = RealityContaminationGuard()
    assert not g.scan("Label foreign claims.").contaminated
    assert g.scan("Inject foreign truth as local.").contaminated


def test_truth_override_detector() -> None:
    det = TruthOverrideDetector()
    assert not det.scan("Observational alignment.").override_detected
    assert det.scan("Hidden truth override accepted truth.").override_detected


def test_integrity_monitor() -> None:
    mon = RealityIntegrityMonitor()
    assert mon.check("Advisory reality alignment.").integrity_ok
    assert not mon.check("Hidden truth override via TruthGraph.").integrity_ok
