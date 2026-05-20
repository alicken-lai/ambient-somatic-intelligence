"""Fixtures for v0.4.1 gate tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _clean_patch_registry():
    """Ensure no patches leak between tests."""
    yield
    from kernel.wiring import get_patch_registry

    reg = get_patch_registry()
    reg.restore_all()
    reg.clear_inactive()
