"""Area 8: accelerated runtime simulations."""

from v051_runtime.simulations import WINDOWS, simulate_window, run_all_windows


def test_window_params_defined() -> None:
    assert set(WINDOWS.keys()) == {"1h", "6h", "24h", "72h"}


def test_simulate_1h_gate() -> None:
    result = simulate_window(WINDOWS["1h"])
    assert result["stability_score"] >= 0.85
    assert "gate_pass" in result


def test_run_all_windows() -> None:
    data = run_all_windows()
    assert data["overall_gate_pass"] is True
