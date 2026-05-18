"""Tests for v0.4 boot verification — All new modules importable, no circular imports."""

from __future__ import annotations

import importlib
import sys


V04_MODULES = [
    # Phase 1 — Skills
    "skills.core.skill_schema",
    "skills.core.skill_registry",
    "skills.core.skill_router",
    "skills.core.skill_validator",
    "skills.compat",
    # Phase 2 — Attention
    "attention.attention_state",
    "attention.salience_engine",
    "attention.novelty_detector",
    "attention.weak_signal_detector",
    "attention.priority_allocator",
    "attention.escalation_router",
    # Phase 3 — Somatic Memory
    "memory.somatic.sensor_episode_store",
    "memory.somatic.environmental_signature",
    "memory.somatic.anomaly_fingerprint",
    "memory.somatic.pattern_similarity",
    "memory.somatic.precursor_matcher",
    # Phase 4 — Skillify
    "agents.skillify.workflow_observer",
    "agents.skillify.pattern_miner",
    "agents.skillify.workflow_cluster",
    "agents.skillify.skill_candidate_generator",
    "agents.skillify.skill_candidate_validator",
    "agents.skillify.skill_registration_pipeline",
]


def test_v04_subsystems_importable() -> None:
    """All new v0.4 modules can be imported without error."""
    failures: list[str] = []
    for module_name in V04_MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            failures.append(f"{module_name}: {exc}")

    assert not failures, f"Failed to import:\n" + "\n".join(failures)


def test_no_circular_imports() -> None:
    """Verify no circular import issues among new modules.

    Strategy: clear cached modules, re-import in reverse order to
    surface any latent circular dependencies.
    """
    to_clear = [m for m in sys.modules if any(
        m.startswith(prefix) for prefix in
        ("skills.", "attention.", "memory.somatic.", "agents.skillify.")
    )]
    saved = {}
    for m in to_clear:
        saved[m] = sys.modules.pop(m)

    failures: list[str] = []
    try:
        for module_name in reversed(V04_MODULES):
            try:
                importlib.import_module(module_name)
            except ImportError as exc:
                failures.append(f"{module_name}: {exc}")
    finally:
        for m in to_clear:
            if m in saved:
                sys.modules[m] = saved[m]

    assert not failures, f"Circular import detected:\n" + "\n".join(failures)
