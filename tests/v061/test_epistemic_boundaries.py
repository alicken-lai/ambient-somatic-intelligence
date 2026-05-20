"""Area 3: epistemic and replay boundaries."""

from governance.constitution.constitutional_guard import ConstitutionalContext, ConstitutionalGuard


def test_certainty_claim_blocked() -> None:
    guard = ConstitutionalGuard()
    v = guard.evaluate(
        ConstitutionalContext(raw_confidence=1.0, certainty_claim=True)
    )
    assert v.compliant is False


def test_replay_executes_blocked() -> None:
    guard = ConstitutionalGuard()
    v = guard.evaluate(ConstitutionalContext(replay_executes=True))
    assert v.compliant is False
    assert any(x.rule_id == "replay_boundary" for x in v.violations)
