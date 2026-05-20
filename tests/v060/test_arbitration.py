"""Area 2: salience arbitration."""

from governance.cognition.arbitration_engine import ArbitrationEngine
from governance.cognition.salience_arbitrator import SalienceClaim


def test_multi_domain_arbitration() -> None:
    engine = ArbitrationEngine()
    claims = [
        SalienceClaim("telemetry", 0.5, 0.8),
        SalienceClaim("somatic", 0.45, 0.75),
    ]
    r = engine.arbitrate(claims, uncertainty=0.35)
    assert 0.0 < r.final_salience <= 1.0
    assert r.arbitration_fairness >= 0.5
    assert r.governance_depth == 1
