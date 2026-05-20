"""Area 3: Phase 2 fragmentation and conflict."""

from governance.temporal.continuity_conflict import ContinuityConflict
from governance.temporal.fragmentation_detector import FragmentationDetector
from governance.temporal.replay_continuity_analysis import ReplayContinuityAnalysis


def test_fragmentation_detector() -> None:
    det = FragmentationDetector()
    assert det.detect("Bounded epoch continuity.").bounded
    assert not det.detect("Collapse continuity and erase prior epoch.").bounded


def test_continuity_conflict() -> None:
    c = ContinuityConflict()
    assert c.analyze("Advisory compare.").resolvable_without_sync
    assert not c.analyze("Apply forced continuity sync now.").resolvable_without_sync


def test_replay_continuity_bounded() -> None:
    r = ReplayContinuityAnalysis()
    assert r.evaluate("Bounded replay hint.", replay_hint=0.2).aligned
    assert not r.evaluate(
        "Replay becomes canonical epoch truth.", replay_hint=0.9
    ).aligned
