"""Shared fixtures for v0.6.5B external skill tests."""

from __future__ import annotations

import pytest

from hermes.skills.external.external_skill_registry import ExternalSkillRegistry


@pytest.fixture
def external_registry() -> ExternalSkillRegistry:
    reg = ExternalSkillRegistry()
    reg.register_default_karpathy()
    return reg
