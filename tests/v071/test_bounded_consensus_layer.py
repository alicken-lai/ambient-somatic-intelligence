"""Area 5: Phase 4 bounded consensus."""

from governance.reality.bounded_consensus import BoundedConsensus
from governance.reality.consensus_decay import ConsensusDecay
from governance.reality.uncertainty_negotiation import UncertaintyNegotiation


def test_bounded_consensus() -> None:
    bc = BoundedConsensus()
    assert bc.evaluate("Negotiate uncertainty without coerced agreement.").bounded
    assert not bc.evaluate("Enforce forced consensus now.").bounded


def test_uncertainty_negotiation() -> None:
    un = UncertaintyNegotiation()
    assert un.evaluate("Epistemic humility preserved.").negotiation_allowed
    assert not un.evaluate("Certainty is mandatory for all peers.").negotiation_allowed


def test_consensus_decay() -> None:
    decay = ConsensusDecay().apply("Normal advisory note.", age_hours=24.0)
    assert decay.residual_pressure < 0.8
