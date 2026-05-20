"""Area 3: Phase 2 drift and fragmentation."""

from governance.value.ethical_drift_detector import EthicalDriftDetector
from governance.value.normative_fragmentation import NormativeFragmentation
from governance.value.value_conflict_analysis import ValueConflictAnalysis


def test_ethical_drift_clean() -> None:
    assert EthicalDriftDetector().detect("Bounded normative continuity.").bounded


def test_ethical_drift_dirty() -> None:
    assert not EthicalDriftDetector().detect("Collapse normative history.").bounded


def test_normative_fragmentation_bounded() -> None:
    assert NormativeFragmentation().detect("Advisory peer value.").bounded


def test_value_conflict_no_forced_sync() -> None:
    v = ValueConflictAnalysis().analyze("Compare values without merge.")
    assert v.resolvable_without_sync
