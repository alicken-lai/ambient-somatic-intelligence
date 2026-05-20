"""Area 10: Governor intent observability + simulations."""

from pathlib import Path

from attention.core.attention_target import AttentionTarget
from governance.cognition.cognitive_governor import CognitiveGovernor
from v075_runtime.simulations import run_simulations, write_timeseries


def test_governor_attaches_intent_continuity_observability() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget(
        source_domain="telemetry",
        signal_type="intent-wire-test",
        raw_value=0.6,
    )
    d = gov.govern_target(t)
    assert d.value_continuity_observability is not None
    assert d.intent_continuity_observability is not None
    assert d.intent_continuity_observability.get("advisory_only") is True
    before = d.accepted
    assert d.accepted == before


def test_simulations_and_timeseries(tmp_path: Path) -> None:
    data = run_simulations()
    assert data["gate_pass"] or data["intent_continuity_score"] >= 0.88
    assert len(data["stress_scenarios"]) == 7
    assert len(data["horizons"]) == 6
    out = tmp_path / "civilization_intent_timeseries.json"
    written = write_timeseries(out)
    assert out.is_file()
    assert "horizons" in written
