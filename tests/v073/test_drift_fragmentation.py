"""Area 3: Phase 2 drift and fragmentation."""

from governance.meaning.meaning_drift_detector import MeaningDriftDetector
from governance.meaning.semantic_conflict_analysis import SemanticConflictAnalysis
from governance.meaning.symbolic_fragmentation import SymbolicFragmentation


def test_drift_detector_clean() -> None:
    v = MeaningDriftDetector().detect("Bounded concept continuity with advisory drift.")
    assert v.bounded


def test_symbolic_fragmentation_dirty() -> None:
    v = SymbolicFragmentation().detect("Collapse meaning and erase prior concept.")
    assert not v.bounded


def test_semantic_conflict_forced_sync() -> None:
    v = SemanticConflictAnalysis().analyze("Apply forced symbolic sync across peers.")
    assert not v.resolvable_without_sync
