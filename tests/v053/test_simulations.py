"""Area 8: accelerated forecast simulations."""

from v053_runtime.simulations import WINDOWS, run_all_windows, simulate_window


def test_windows_defined() -> None:
    assert set(WINDOWS.keys()) == {"6h", "24h", "7d", "30d"}


def test_simulate_6h() -> None:
    r = simulate_window(WINDOWS["6h"])
    assert r["stability_score"] >= 0.85


def test_run_all_windows() -> None:
    data = run_all_windows()
    assert data["overall_gate_pass"] is True
