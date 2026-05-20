"""Area 8: accelerated memory simulations."""

from v052_runtime.simulations import WINDOWS, run_all_windows, simulate_window


def test_windows_defined() -> None:
    assert set(WINDOWS.keys()) == {"1d", "7d", "30d", "90d"}


def test_simulate_1d() -> None:
    r = simulate_window(WINDOWS["1d"])
    assert r["stability_score"] >= 0.85


def test_run_all_windows() -> None:
    data = run_all_windows()
    assert data["overall_gate_pass"] is True
