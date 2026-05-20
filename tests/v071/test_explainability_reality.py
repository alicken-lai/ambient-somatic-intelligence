"""Area 7: Phase 6 explainability."""

from attention.explainability.consensus_breakdown import ConsensusBreakdown
from attention.explainability.divergence_explainer import DivergenceExplainer
from attention.explainability.reality_alignment_reasoning import RealityAlignmentReasoning


def test_reality_alignment_reasoning() -> None:
    out = RealityAlignmentReasoning().explain("Advisory bounded alignment.")
    assert out["advisory_only"] is True
    assert out["aligned"] is True


def test_divergence_explainer() -> None:
    out = DivergenceExplainer().explain(
        "Compare peers.",
        left_claim="local ops",
        right_claim="foreign ops",
    )
    assert out["merge_forbidden"] is True
    assert "exchange" in out


def test_consensus_breakdown() -> None:
    out = ConsensusBreakdown().explain("Negotiate uncertainty across peers.")
    assert out["forced_consensus_blocked"] is True
