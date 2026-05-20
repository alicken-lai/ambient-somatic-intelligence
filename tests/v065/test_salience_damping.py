"""Area 4: salience damping advisory."""

from governance.homeostasis.salience_damping import SalienceDamping


def test_advisory_damp_bounded() -> None:
    d = SalienceDamping()
    for sal in (0.5, 0.9, 0.3, 0.85):
        d.record_salience(sal)
    factor = d.advisory_damp_factor(governed_salience=0.85)
    assert factor <= 0.35
