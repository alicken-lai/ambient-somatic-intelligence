"""Unit tests for the v0.5 supporting subpackages.

Covers attention.competition, attention.memory, attention.explainability and
attention.somatic — the modules that complete the v050 attention surface.
"""

from __future__ import annotations

import math

from attention.attention_state import AttentionSignal
from attention.competition.salience_competition import (
    SalienceCompetition,
    jain_fairness,
)
from attention.core.attention_target import AttentionTarget
from attention.core.salience_factor import ALL_DIMENSIONS
from attention.explainability.explain_attention import explain_attention
from attention.kernel.salience_engine import KernelSalienceEngine
from attention.memory.recall_salience import RecallSalience
from attention.somatic.somatic_attention_adapter import SomaticAttentionAdapter


# --------------------------------------------------------------------------
# competition
# --------------------------------------------------------------------------

def test_competition_picks_winner_and_is_fair() -> None:
    comp = SalienceCompetition()
    a = AttentionTarget("somatic", "a", 0.9)
    b = AttentionTarget("task", "b", 0.2)
    report = comp.compete_with_report([(a, 0.9), (b, 0.2)])
    assert a in report.winners
    assert report.fairness_score >= 0.5


def test_competition_always_admits_at_least_one() -> None:
    comp = SalienceCompetition(budget=0.1)
    a = AttentionTarget("somatic", "a", 0.9)
    report = comp.compete_with_report([(a, 0.9)])
    assert len(report.winners) == 1


def test_jain_fairness_equal_is_one() -> None:
    assert math.isclose(jain_fairness([0.5, 0.5, 0.5]), 1.0)
    assert jain_fairness([]) == 1.0


# --------------------------------------------------------------------------
# memory
# --------------------------------------------------------------------------

def test_recall_salience_with_tags() -> None:
    rs = RecallSalience()
    rs.resonance.record("memory", "recall_hit", 0.9)
    t = AttentionTarget("memory", "recall_hit", 0.5, metadata={"tags": ["a", "b"]})
    assert rs.score(t, recent_tags=["a"]) > 0


def test_recall_resonance_boosts_score() -> None:
    rs = RecallSalience()
    t = AttentionTarget("memory", "hit", 0.3)
    before = rs.score(t)
    rs.resonance.record("memory", "hit", 1.0)
    assert rs.score(t) > before


# --------------------------------------------------------------------------
# explainability
# --------------------------------------------------------------------------

def test_explain_attention_has_ten_children() -> None:
    sv = KernelSalienceEngine().compute(AttentionTarget("governance", "alert", 0.8))
    expl = explain_attention(sv)
    assert expl.dominant_factor is not None
    assert len(expl.breakdown.children) == 10
    assert {c.name for c in expl.breakdown.children} == set(ALL_DIMENSIONS)


# --------------------------------------------------------------------------
# somatic
# --------------------------------------------------------------------------

def test_somatic_adapter_sets_severity() -> None:
    adapter = SomaticAttentionAdapter()
    adapter.update_stress(0.7)
    target = adapter.from_signal(AttentionSignal("somatic", "heat", 0.6))
    assert target.metadata.get("somatic_severity", 0) > 0


def test_somatic_adapter_higher_stress_raises_severity() -> None:
    low = SomaticAttentionAdapter()
    low.update_stress(0.1)
    high = SomaticAttentionAdapter()
    high.update_stress(0.9)
    sig = AttentionSignal("somatic", "heat", 0.6)
    assert (
        high.from_signal(sig).metadata["somatic_severity"]
        > low.from_signal(sig).metadata["somatic_severity"]
    )
