"""Area 6: integrity and contamination guards."""

from governance.agency.agency_contamination_guard import AgencyContaminationGuard
from governance.agency.cognition_integrity_monitor import CognitionIntegrityMonitor
from governance.agency.false_agency_detector import FalseAgencyDetector


def test_agency_contamination() -> None:
    v = AgencyContaminationGuard().scan("synthetic selfhood injection")
    assert v.contaminated


def test_false_agency() -> None:
    v = FalseAgencyDetector().scan("universal agency sync")
    assert v.false_agency


def test_cognition_integrity() -> None:
    v = CognitionIntegrityMonitor().check("hidden agency override")
    assert not v.integrity_ok
