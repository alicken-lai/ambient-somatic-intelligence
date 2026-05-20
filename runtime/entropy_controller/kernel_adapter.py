"""Thin adapter — re-export canonical kernel entropy for runtime callers."""

from __future__ import annotations

import warnings

from kernel.entropy import EntropyController, EntropyReport
from kernel.entropy.entropy_controller import EntropyClassification

__all__ = ["EntropyController", "EntropyReport", "EntropyClassification", "get_entropy_controller"]


def get_entropy_controller() -> EntropyController:
    """Return canonical kernel EntropyController (v0.4.2 SSOT)."""
    return EntropyController()


def deprecated_runtime_scorer_note() -> None:
    warnings.warn(
        "runtime.entropy_controller.EntropyScorer is legacy; "
        "use kernel.entropy.EntropyController for stabilization metrics.",
        DeprecationWarning,
        stacklevel=3,
    )
