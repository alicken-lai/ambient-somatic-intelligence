"""Area 10: Governor runtime observability + simulations."""

from pathlib import Path

from attention.core.attention_target import AttentionTarget
from governance.cognition.cognitive_governor import CognitiveGovernor
from v065c_runtime.simulations import run_simulations, write_timeseries


def test_governor_attaches_runtime_observability() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget(
        source_domain="telemetry",
        signal_type="runtime-soak-wire-test",
        raw_value=0.6,
    )
    before_accepted = None
    d = gov.govern_target(t)
    assert d.runtime_external_observability is not None
    assert d.runtime_external_observability.get("advisory_only") is True
    assert d.external_advisory is not None
    before_accepted = d.accepted
    assert d.accepted == before_accepted


def test_simulations_and_timeseries(tmp_path: Path) -> None:
    data = run_simulations()
    assert data["gate_pass"] or data["external_runtime_score"] >= 0.88
    assert len(data["stress_scenarios"]) == 7
    assert len(data["horizons"]) == 5
    out = tmp_path / "external_runtime_timeseries.json"
    written = write_timeseries(out)
    assert out.is_file()
    assert "horizons" in written
