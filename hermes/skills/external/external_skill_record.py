"""Record for a mounted external skill with provenance."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from hermes.skills.external.external_skill_status import ExternalSkillStatus


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ExternalSkillRecord:
    skill_id: str
    name: str
    source_url: str
    source_commit: str = "main"
    status: ExternalSkillStatus = ExternalSkillStatus.IMPORTED
    mount_path: str = ""
    filter_notes: list[str] = field(default_factory=list)
    compatibility_score: float = 0.0
    provenance_hash: str = ""
    mounted_at: str = field(default_factory=_utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "source_url": self.source_url,
            "source_commit": self.source_commit,
            "status": self.status.value,
            "mount_path": self.mount_path,
            "filter_notes": list(self.filter_notes),
            "compatibility_score": round(self.compatibility_score, 4),
            "provenance_hash": self.provenance_hash,
            "mounted_at": self.mounted_at,
            "metadata": dict(self.metadata),
        }
