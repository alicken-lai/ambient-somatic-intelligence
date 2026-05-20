"""Area 4: constitutional coherence."""

from governance.coherence.constitutional_coherence import ConstitutionalCoherence


def test_compliant_low_pressure() -> None:
    checker = ConstitutionalCoherence()
    assert checker.coherent(constitutional_compliant=True, constitutional_verdict={}) is True


def test_non_compliant_high_pressure() -> None:
    checker = ConstitutionalCoherence()
    p = checker.pressure(
        constitutional_compliant=False,
        constitutional_verdict={"violations": ["test"]},
    )
    assert p >= 0.5
