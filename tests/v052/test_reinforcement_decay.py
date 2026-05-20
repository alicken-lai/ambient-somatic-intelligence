"""Area 3: reinforcement ceiling and anomaly decay."""

from datetime import datetime, timedelta, timezone

from attention.consolidation.anomaly_decay import AnomalyDecay
from attention.consolidation.precursor_weighting import PrecursorWeighting
from attention.consolidation.salience_reinforcement import REINFORCEMENT_CEILING, SalienceReinforcement
from attention.core.precursor_signal import PrecursorSignal


def test_reinforcement_ceiling() -> None:
    r = SalienceReinforcement()
    v = r.reinforce(0.95, 0.9, hit_count=100)
    assert v <= REINFORCEMENT_CEILING


def test_precursor_weighting_bounded() -> None:
    w = PrecursorWeighting()
    p = PrecursorSignal(pattern_id="p1", strength=0.8, domain="somatic")
    assert w.weight(p) <= 1.0


def test_anomaly_decay() -> None:
    d = AnomalyDecay()
    old = datetime.now(timezone.utc) - timedelta(seconds=600)
    assert d.apply(0.9, old) < 0.5
