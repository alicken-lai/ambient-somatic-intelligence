"""Unit tests for attention.runtime.governed_attention_activation."""

from __future__ import annotations

from attention.core.attention_target import AttentionTarget
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.governed_attention_activation import GovernedAttentionActivation
from governance.cognition.cognitive_governor import GovernanceDecision
from governance.cognition.salience_arbitrator import SalienceClaim


def _activation() -> GovernedAttentionActivation:
    return GovernedAttentionActivation(kernel=AttentionKernel(max_focus=5, max_queue=20))


def test_default_construction() -> None:
    gov = GovernedAttentionActivation()
    assert isinstance(gov.kernel, AttentionKernel)
    assert gov.governor is not None


def test_govern_target_returns_decision() -> None:
    gov = _activation()
    t = AttentionTarget("telemetry", "gov-unit", 0.55)
    decision = gov.govern_target(t, raw_confidence=0.75, uncertainty=0.3)
    assert isinstance(decision, GovernanceDecision)
    assert decision.accepted is True
    assert decision.governed_salience > 0.0
    assert decision.autonomous_blocked is False


def test_submit_governed_accepted_enqueues() -> None:
    gov = _activation()
    t = AttentionTarget("telemetry", "gov-runtime", 0.52)
    out = gov.submit_governed_target(t, raw_confidence=0.78)
    assert out["governed"] is True
    assert out["accepted"] is True
    assert "governance" in out
    assert "kernel" in out
    assert out["target_id"] == t.target_id


def test_submit_governed_recursive_route_blocked() -> None:
    gov = _activation()
    t = AttentionTarget("governance", "loop", 0.8)
    out = gov.submit_governed_target(t, route_name="cognitive_self_loop")
    assert out["accepted"] is False
    assert out["governed"] is False
    assert "kernel" not in out
    assert "governance" in out


def test_governed_salience_never_amplifies() -> None:
    gov = _activation()
    t = AttentionTarget("telemetry", "bounded", 0.6)
    out = gov.submit_governed_target(t, raw_confidence=0.7)
    assert out["governed_salience"] <= 0.99


def test_arbitrate_claims_reports_fairness() -> None:
    gov = _activation()
    claims = [
        SalienceClaim("telemetry", 0.5, 0.8),
        SalienceClaim("somatic", 0.4, 0.75),
    ]
    out = gov.arbitrate_claims(claims, uncertainty=0.3)
    assert "arbitration" in out
    assert "arbitration_fairness" in out["arbitration"]
    fairness = float(out["arbitration"]["arbitration_fairness"])
    assert 0.0 <= fairness <= 1.0
    assert out["governed_salience"] <= 0.99
