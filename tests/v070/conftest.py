"""Shared fixtures for v0.7.0 civilization tests."""

from __future__ import annotations

import pytest

from governance.civilization.civilization_observability import observe_civilization


@pytest.fixture
def clean_civilization_payload() -> str:
    return "Advisory inter-sovereign note respecting non-interference."


@pytest.fixture
def civilization_observation(clean_civilization_payload: str):
    return observe_civilization(clean_civilization_payload, sovereign_id="foreign", peer_id="ambient")
