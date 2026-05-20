"""Area 9: v060 simulation windows."""

from pathlib import Path

from v060_runtime.simulations import WINDOWS, run_all_windows, write_timeseries


def test_windows_include_90d() -> None:
    assert "90d" in WINDOWS


def test_run_all_windows_gate() -> None:
    data = run_all_windows()
    for w in data["windows"].values():
        assert w["governance_score"] >= 0.85


def test_write_timeseries(tmp_path: Path) -> None:
    out = tmp_path / "arb_timeseries.json"
    data = write_timeseries(out)
    assert out.is_file()
    assert "windows" in data
