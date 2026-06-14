"""Routing policy constraints that optimization may not weaken."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoutingPolicyConfig:
    minimum_sample_threshold: int = 3
    confidence_threshold: float = 0.6
    quality_margin: float = 3.0
    rollback_margin: float = -5.0


IMMUTABLE_GOVERNANCE_RULES = {
    "guardian_rules",
    "provider_permissions",
    "credential_access_policies",
    "memory_write_policies",
    "human_approval_requirements",
}
