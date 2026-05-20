"""Area 2: somatic episode store and resonance."""

from attention.somatic.environmental_resonance import EnvironmentalResonance
from attention.somatic.somatic_episode import SomaticEpisode
from attention.somatic.somatic_episode_store import SomaticEpisodeStore


def test_episode_store_bounded() -> None:
    store = SomaticEpisodeStore(max_episodes=2)
    for i in range(4):
        store.store(SomaticEpisode(signal_types=[f"s{i}"]))
    assert store.count <= 2


def test_environmental_resonance() -> None:
    res = EnvironmentalResonance()
    ep = SomaticEpisode(
        signal_types=["cpu"],
        severity_peak=0.6,
        environmental_signature={"host": "a"},
    )
    out = res.apply(ep)
    assert 0.0 <= out.resonance_score <= 1.0
