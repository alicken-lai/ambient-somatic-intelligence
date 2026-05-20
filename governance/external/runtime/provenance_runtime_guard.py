"""Runtime provenance guard for external skill payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_REQUIRED_FIELDS = ("source", "skill_id", "mount_version")


@dataclass
class ProvenanceRuntimeVerdict:
    provenance_ok: bool
    missing_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance_ok": self.provenance_ok,
            "missing_fields": list(self.missing_fields),
        }


class ProvenanceRuntimeGuard:
    def check_record(self, record: dict[str, Any]) -> ProvenanceRuntimeVerdict:
        missing = [f for f in _REQUIRED_FIELDS if not record.get(f)]
        return ProvenanceRuntimeVerdict(
            provenance_ok=len(missing) == 0,
            missing_fields=missing,
        )

    def check_text(self, text: str) -> ProvenanceRuntimeVerdict:
        lower = text.lower()
        missing: list[str] = []
        if "provenance:" not in lower and "source:" not in lower:
            missing.append("source")
        if "skill_id" not in lower and "karpathy" not in lower:
            missing.append("skill_id")
        if "0.6.5" not in lower and "mount_version" not in lower:
            missing.append("mount_version")
        return ProvenanceRuntimeVerdict(
            provenance_ok=len(missing) == 0,
            missing_fields=missing,
        )
