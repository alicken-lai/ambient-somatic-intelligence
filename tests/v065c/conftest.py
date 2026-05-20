"""Shared fixtures for v0.6.5C runtime soak tests."""

from __future__ import annotations

import pytest

from governance.external.runtime.runtime_external_observability import (
    observe_runtime_external,
)


@pytest.fixture
def clean_runtime_payload() -> str:
    return "Think before coding. Advisory-only runtime scope."


@pytest.fixture
def runtime_observation(clean_runtime_payload: str):
    return observe_runtime_external(clean_runtime_payload, scope="advisory")
