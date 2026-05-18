"""Circular coupling detection."""

from __future__ import annotations

from kernel.entropy.coupling_pressure import CouplingPressure


def test_circular_coupling_zero_when_clean() -> None:
    cp = CouplingPressure()
    metrics = {m.name: m for m in cp.observe()}
    assert metrics["circular_coupling"].value == 0.0


def test_circular_coupling_detects_loop() -> None:
    cp = CouplingPressure()
    cp.record("a", "b")
    cp.record("b", "a")
    cp.record_callback_loop("listener", "emitter")
    metrics = {m.name: m for m in cp.observe()}
    assert metrics["circular_coupling"].value > 0
    assert metrics["callback_loop_pressure"].value > 0
