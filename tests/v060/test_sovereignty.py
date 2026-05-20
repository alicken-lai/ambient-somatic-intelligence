"""Area 3: sovereignty limits."""

from governance.cognition.sovereignty_limits import MAX_DOMAIN_SHARE, SovereigntyLimitsChecker


def test_monopolization_detected() -> None:
    checker = SovereigntyLimitsChecker()
    report = checker.check_domain_shares({"telemetry": 0.9, "somatic": 0.1})
    assert report.monopolization_violation is True
    assert report.compliant is False


def test_balanced_shares_compliant() -> None:
    checker = SovereigntyLimitsChecker()
    report = checker.check_domain_shares({"telemetry": 0.35, "somatic": 0.35, "memory": 0.3})
    assert report.max_share_observed <= MAX_DOMAIN_SHARE + 0.01
    assert report.compliant is True
