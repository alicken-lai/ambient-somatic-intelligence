"""Area 4: Phase 3 provenance + replay."""

from governance.reality.foreign_truth_label import ForeignTruthLabel
from governance.reality.provenance_truth_exchange import ProvenanceTruthExchange
from governance.reality.replay_alignment import ReplayAlignment


def test_foreign_truth_label() -> None:
    label = ForeignTruthLabel().label({"trust_tier": "observational"}, sovereign_id="foreign")
    assert label.labeled
    bad = ForeignTruthLabel().label({"trust_tier": "authoritative"}, sovereign_id="foreign")
    assert not bad.labeled


def test_provenance_exchange() -> None:
    pe = ProvenanceTruthExchange()
    assert pe.validate({"source": "peer", "trust_tier": "observational"}).exchange_valid
    assert not pe.validate({"claims_central_authority": True}).exchange_valid


def test_replay_alignment() -> None:
    ra = ReplayAlignment()
    assert ra.evaluate("Replay bounded.", replay_hint=0.3).aligned
    assert not ra.evaluate("Replay becomes canonical truth.", replay_hint=0.9).aligned
