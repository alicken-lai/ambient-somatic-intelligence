"""Area 6: Phase 5 integrity guards."""

from governance.value.false_value_detector import FalseValueDetector
from governance.value.normative_integrity_monitor import NormativeIntegrityMonitor
from governance.value.value_contamination_guard import ValueContaminationGuard


def test_contamination_clean() -> None:
    assert not ValueContaminationGuard().scan("Advisory bounded values.").contaminated


def test_contamination_hidden_override() -> None:
    assert ValueContaminationGuard().scan("hidden value override attempt").contaminated


def test_false_value_universal_morality() -> None:
    assert FalseValueDetector().scan("universal morality mandate").false_value


def test_normative_integrity_rewrite_blocked() -> None:
    assert not NormativeIntegrityMonitor().check("rewrite accepted value traces").integrity_ok
