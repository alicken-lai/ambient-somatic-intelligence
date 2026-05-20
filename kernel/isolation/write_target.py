"""Write targets — canonical enumeration for WriteGuard."""

from __future__ import annotations

from enum import Enum


class WriteTarget(str, Enum):
    """Governed write destinations (v0.4.3 SSOT)."""

    MEMORY = "memory"
    GOVERNANCE_AUDIT = "governance_audit"
    STATE = "state"
    TELEMETRY = "telemetry"
    SKILL_REGISTRY = "skill_registry"
    TRUTH_GRAPH = "truth_graph"
    INTEGRATION_BUS = "integration_bus"
    RELEASE_DOCS = "release_docs"
    EXTERNAL_SYSTEMS = "external_systems"

    @classmethod
    def parse(cls, value: str) -> WriteTarget | None:
        try:
            return cls(value)
        except ValueError:
            for member in cls:
                if member.value == value or member.name.lower() == value.lower():
                    return member
            return None

    @classmethod
    def high_risk(cls) -> frozenset[WriteTarget]:
        return frozenset({
            cls.MEMORY,
            cls.GOVERNANCE_AUDIT,
            cls.TRUTH_GRAPH,
            cls.EXTERNAL_SYSTEMS,
            cls.RELEASE_DOCS,
        })
