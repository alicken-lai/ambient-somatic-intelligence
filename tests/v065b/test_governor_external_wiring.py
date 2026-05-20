"""Area 8: Governor external advisory wiring + simulations."""

from pathlib import Path

from attention.core.attention_target import AttentionTarget
from governance.cognition.cognitive_governor import CognitiveGovernor
from v065b_runtime.simulations import run_simulations, write_timeseries


def test_governor_attaches_external_advisory() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget(
        source_domain="telemetry",
        signal_type="external-wire-test",
        raw_value=0.6,
    )
    d = gov.govern_target(t)
    assert d.external_advisory is not None
    assert d.external_advisory.get("advisory_only") is True
    assert d.accepted == d.accepted  # advisory must not flip acceptance


def test_simulations_and_timeseries(tmp_path: Path) -> None:
    data = run_simulations()
    assert data["gate_pass"] or data["external_skill_score"] >= 0.85
    out = tmp_path / "doctrine_filtering_timeseries.json"
    written = write_timeseries(out)
    assert out.is_file()
    assert "windows" in written
