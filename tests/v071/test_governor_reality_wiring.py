"""Area 10: Governor reality observability + simulations."""

from pathlib import Path

from attention.core.attention_target import AttentionTarget
from governance.cognition.cognitive_governor import CognitiveGovernor
from v071_runtime.simulations import run_simulations, write_timeseries


def test_governor_attaches_reality_alignment_observability() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget(
        source_domain="telemetry",
        signal_type="reality-wire-test",
        raw_value=0.6,
    )
    d = gov.govern_target(t)
    assert d.civilization_observability is not None
    assert d.reality_alignment_observability is not None
    assert d.reality_alignment_observability.get("advisory_only") is True
    before = d.accepted
    assert d.accepted == before


def test_simulations_and_timeseries(tmp_path: Path) -> None:
    data = run_simulations()
    assert data["gate_pass"] or data["reality_alignment_score"] >= 0.88
    assert len(data["stress_scenarios"]) == 7
    assert len(data["horizons"]) == 5
    out = tmp_path / "cross_runtime_reality_timeseries.json"
    written = write_timeseries(out)
    assert out.is_file()
    assert "horizons" in written
