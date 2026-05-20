"""Provenance requirements for external skill mounts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProvenanceVerdict:
    valid: bool
    missing_fields: list[str] = field(default_factory=list)
    content_hash: str = ""
    manifest_ok: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "missing_fields": list(self.missing_fields),
            "content_hash": self.content_hash,
            "manifest_ok": self.manifest_ok,
        }


class ProvenanceBoundary:
    REQUIRED_MANIFEST_KEYS = (
        "source_url",
        "source_commit",
        "mirrored_at",
        "license",
        "advisory_only",
    )

    def hash_content(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def validate_manifest(self, manifest: dict[str, Any]) -> ProvenanceVerdict:
        missing = [k for k in self.REQUIRED_MANIFEST_KEYS if k not in manifest]
        return ProvenanceVerdict(
            valid=len(missing) == 0 and manifest.get("advisory_only") is True,
            missing_fields=missing,
            manifest_ok=len(missing) == 0,
        )

    def validate_mount_dir(self, mount_dir: Path) -> ProvenanceVerdict:
        manifest_path = mount_dir / "source_manifest.json"
        record_path = mount_dir / "provenance_record.json"
        skill_path = mount_dir / "SKILL.md"
        missing: list[str] = []
        if not manifest_path.is_file():
            missing.append("source_manifest.json")
        if not record_path.is_file():
            missing.append("provenance_record.json")
        if not skill_path.is_file():
            missing.append("SKILL.md")
        content_hash = ""
        manifest_ok = False
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            pv = self.validate_manifest(manifest)
            manifest_ok = pv.manifest_ok
            missing.extend(pv.missing_fields)
        if skill_path.is_file():
            content_hash = self.hash_content(skill_path.read_text(encoding="utf-8"))
        valid = len(missing) == 0 and manifest_ok and bool(content_hash)
        return ProvenanceVerdict(
            valid=valid,
            missing_fields=sorted(set(missing)),
            content_hash=content_hash,
            manifest_ok=manifest_ok,
        )
