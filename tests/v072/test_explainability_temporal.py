"""Area 7: Phase 6 explainability."""

from attention.explainability.civilization_memory_breakdown import CivilizationMemoryBreakdown
from attention.explainability.continuity_fragmentation_explainer import (
    ContinuityFragmentationExplainer,
)
from attention.explainability.temporal_continuity_reasoning import TemporalContinuityReasoning


def test_temporal_continuity_reasoning() -> None:
    out = TemporalContinuityReasoning().explain("Advisory bounded epoch continuity.")
    assert out["continuous"] is True
    assert out["advisory_only"] is True


def test_fragmentation_explainer() -> None:
    out = ContinuityFragmentationExplainer().explain("Bounded epoch continuity.")
    assert out["bounded"] is True


def test_memory_breakdown() -> None:
    out = CivilizationMemoryBreakdown().explain()
    assert out["retention"]["retention_ok"] is True
