"""External skill lifecycle states — advisory mount only."""

from __future__ import annotations

from enum import Enum


class ExternalSkillStatus(str, Enum):
    IMPORTED = "IMPORTED"
    FILTERED = "FILTERED"
    COMPATIBLE = "COMPATIBLE"
    RESTRICTED = "RESTRICTED"
    BLOCKED = "BLOCKED"

    def is_advisory_allowed(self) -> bool:
        return self in {
            ExternalSkillStatus.COMPATIBLE,
            ExternalSkillStatus.RESTRICTED,
        }

    def is_blocked(self) -> bool:
        return self == ExternalSkillStatus.BLOCKED
