"""Tests for backward compatibility — Existing v0.3 modules still work."""

from __future__ import annotations


def test_existing_imports_work() -> None:
    """All existing __init__.py exports are still accessible."""
    import somatic
    import governance
    import memory
    import agents

    assert somatic is not None
    assert governance is not None
    assert memory is not None
    assert agents is not None


def test_somatic_signal_types_unchanged() -> None:
    """SignalType enum values from somatic.signal_bus are preserved."""
    from somatic.signal_bus import SignalType

    assert hasattr(SignalType, "PRESSURE")
    assert hasattr(SignalType, "PAIN")
    assert hasattr(SignalType, "FATIGUE")
    assert hasattr(SignalType, "ALERTNESS")
    assert hasattr(SignalType, "CALM")
    assert hasattr(SignalType, "REFLEX")

    assert SignalType.PRESSURE.value == "pressure"
    assert SignalType.PAIN.value == "pain"


def test_attention_level_unchanged() -> None:
    """AttentionLevel enum values from somatic.attention_manager are preserved."""
    from somatic.attention_manager import AttentionLevel

    assert hasattr(AttentionLevel, "FOCUSED")
    assert hasattr(AttentionLevel, "ALERT")
    assert hasattr(AttentionLevel, "STRESSED")
    assert hasattr(AttentionLevel, "OVERWHELMED")

    assert int(AttentionLevel.FOCUSED) == 0
    assert int(AttentionLevel.ALERT) == 1
    assert int(AttentionLevel.STRESSED) == 2
    assert int(AttentionLevel.OVERWHELMED) == 3


def test_governance_risk_levels_unchanged() -> None:
    """RiskLevel enum values from governance.policy_engine are preserved."""
    from governance.policy_engine import RiskLevel

    assert hasattr(RiskLevel, "ALLOW")
    assert hasattr(RiskLevel, "REVIEW_REQUIRED")
    assert hasattr(RiskLevel, "BLOCK")

    assert int(RiskLevel.ALLOW) == 0
    assert int(RiskLevel.REVIEW_REQUIRED) == 1
    assert int(RiskLevel.BLOCK) == 2

    assert RiskLevel.from_str("allow") == RiskLevel.ALLOW
    assert RiskLevel.from_str("block") == RiskLevel.BLOCK
