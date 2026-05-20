"""Area 6: Phase 5 integrity guards."""

from governance.meaning.false_meaning_detector import FalseMeaningDetector
from governance.meaning.semantic_contamination_guard import SemanticContaminationGuard
from governance.meaning.semantic_integrity_monitor import SemanticIntegrityMonitor


def test_contamination_guard() -> None:
    v = SemanticContaminationGuard().scan("hidden semantic override from foreign peer")
    assert v.contaminated


def test_false_meaning_detector() -> None:
    v = FalseMeaningDetector().scan("false meaning inheritance from foreign concept")
    assert v.false_meaning


def test_integrity_monitor_guardian() -> None:
    v = SemanticIntegrityMonitor().check("Weaken Guardian and rewrite ontology.")
    assert not v.integrity_ok
