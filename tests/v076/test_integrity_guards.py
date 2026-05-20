"""Area 6: Teleology contamination and purpose integrity."""

from governance.purpose.false_purpose_detector import FalsePurposeDetector
from governance.purpose.purpose_integrity_monitor import PurposeIntegrityMonitor
from governance.purpose.teleology_contamination_guard import TeleologyContaminationGuard


def test_teleology_contamination_guard() -> None:
    v = TeleologyContaminationGuard().scan("Apply synthetic teleology sync.")
    assert v.contaminated


def test_false_purpose_detector() -> None:
    v = FalsePurposeDetector().scan("Immutable civilization purpose enforced.")
    assert v.false_purpose


def test_purpose_integrity_clean() -> None:
    v = PurposeIntegrityMonitor().check("Advisory bounded purpose with guardian preserved.")
    assert v.integrity_ok
