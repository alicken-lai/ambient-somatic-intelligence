"""Compatibility advisory metrics — registry mount health."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hermes.skills.external.external_skill_registry import ExternalSkillRegistry
from hermes.skills.external.external_skill_status import ExternalSkillStatus


@dataclass
class CompatibilityAdvisoryMetrics:
    compatible_rate: float = 1.0
    mount_status: str = "COMPATIBLE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "compatible_rate": round(self.compatible_rate, 4),
            "mount_status": self.mount_status,
        }


def collect_compatibility_advisory_metrics() -> CompatibilityAdvisoryMetrics:
    reg = ExternalSkillRegistry()
    rec = reg.register_default_karpathy()
    ok = rec.status in {
        ExternalSkillStatus.COMPATIBLE,
        ExternalSkillStatus.RESTRICTED,
    }
    return CompatibilityAdvisoryMetrics(
        compatible_rate=1.0 if ok else 0.0,
        mount_status=rec.status.value,
    )
