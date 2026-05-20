"""Area 7: Phase 6 explainability."""

from attention.explainability.civilization_semantic_breakdown import CivilizationSemanticBreakdown
from attention.explainability.meaning_drift_explainer import MeaningDriftExplainer
from attention.explainability.semantic_continuity_reasoning import SemanticContinuityReasoning


def test_semantic_continuity_reasoning() -> None:
    out = SemanticContinuityReasoning().explain("Advisory bounded concept continuity.")
    assert out["continuous"] is True
    assert out["advisory_only"] is True


def test_meaning_drift_explainer() -> None:
    out = MeaningDriftExplainer().explain("Bounded concept continuity.")
    assert out["bounded"] is True


def test_civilization_semantic_breakdown() -> None:
    out = CivilizationSemanticBreakdown().explain()
    assert out["retention"]["retention_ok"] is True
