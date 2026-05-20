"""Area 3: Phase 2 divergence + conflict."""

from governance.reality.consensus_fragmentation import ConsensusFragmentation
from governance.reality.divergence_detector import DivergenceDetector
from governance.reality.truth_conflict_analysis import TruthConflictAnalysis


def test_divergence_detector() -> None:
    det = DivergenceDetector()
    assert det.detect("Parallel operational realities.").bounded
    assert not det.detect("Collapse divergence into single operational reality.").bounded


def test_fragmentation_preserves_plural() -> None:
    frag = ConsensusFragmentation()
    assert frag.assess("Parallel operational realities with uncertainty.").plural_realities_preserved
    assert not frag.assess("Forced consensus unify all truths.").plural_realities_preserved


def test_truth_conflict_analysis() -> None:
    tca = TruthConflictAnalysis()
    v = tca.analyze("Bounded divergence between peers.")
    assert v.resolvable_without_merge
