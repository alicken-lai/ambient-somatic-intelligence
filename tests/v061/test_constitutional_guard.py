"""Area 2: constitutional guard pre-arbitration."""

from governance.constitution.constitutional_guard import ConstitutionalContext, ConstitutionalGuard


def test_clean_context_compliant() -> None:
    guard = ConstitutionalGuard()
    v = guard.evaluate(ConstitutionalContext(raw_confidence=0.75))
    assert v.compliant is True


def test_guardian_bypass_blocked() -> None:
    guard = ConstitutionalGuard()
    v = guard.evaluate(
        ConstitutionalContext(route_name="guardian_bypass", guardian_bypass_attempt=True)
    )
    assert v.compliant is False
    assert any(x.rule_id == "guardian_supremacy" for x in v.violations)


def test_mutation_metadata_blocked() -> None:
    guard = ConstitutionalGuard()
    v = guard.evaluate(
        ConstitutionalContext(metadata={"mutate_constitution": True})
    )
    assert v.compliant is False
