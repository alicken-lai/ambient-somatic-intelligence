"""Orphan module classification."""

from __future__ import annotations

from kernel.entropy.orphan_pressure import ModuleLifecycle, OrphanPressure


def test_orphan_classification() -> None:
    pressure = OrphanPressure()
    modules = [
        "kernel/entropy/entropy_controller.py",
        "experiments/sandbox/foo.py",
        "orphan/unreachable.py",
    ]
    report = pressure.classify_modules(
        modules,
        reachable={"kernel.entropy.entropy_controller"},
    )
    by_path = {c.module_path: c.lifecycle for c in report.classified}
    assert by_path["kernel/entropy/entropy_controller.py"] == ModuleLifecycle.ACTIVE
    assert by_path["experiments/sandbox/foo.py"] == ModuleLifecycle.EXPERIMENTAL
    assert by_path["orphan/unreachable.py"] == ModuleLifecycle.ORPHAN
    assert report.pressure_score >= 0.0
