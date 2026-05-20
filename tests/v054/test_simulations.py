"""Area 7: v054 simulation windows."""

from pathlib import Path

from attention.calibration.confidence_cap import ABSOLUTE_MAX_CONFIDENCE
from v054_runtime.simulations import WINDOWS, run_all_windows, write_timeseries


def test_windows_include_90d() -> None:
    assert "90d" in WINDOWS


def test_run_all_windows_gate() -> None:
    data = run_all_windows()
    for w in data["windows"].values():
        assert w["max_calibrated_confidence"] <= ABSOLUTE_MAX_CONFIDENCE
        assert w["below_absolute_max"] is True


def test_write_timeseries(tmp_path: Path) -> None:
    out = tmp_path / "cal_timeseries.json"
    data = write_timeseries(out)
    assert out.is_file()
    assert "windows" in data
