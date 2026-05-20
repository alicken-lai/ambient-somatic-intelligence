"""Validate runtime provenance chain for external skills."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.external.provenance_boundary import ProvenanceBoundary
from governance.external.runtime.provenance_runtime_guard import ProvenanceRuntimeGuard


@dataclass
class RuntimeProvenanceValidation:
    valid: bool
    runtime_ok: bool
    boundary_ok: bool
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "runtime_ok": self.runtime_ok,
            "boundary_ok": self.boundary_ok,
            "issues": list(self.issues),
        }


class RuntimeProvenanceValidator:
    def __init__(self) -> None:
        self._runtime = ProvenanceRuntimeGuard()
        self._boundary = ProvenanceBoundary()

    def validate(
        self,
        text: str,
        *,
        record: dict[str, Any] | None = None,
    ) -> RuntimeProvenanceValidation:
        issues: list[str] = []
        rt = self._runtime.check_text(text)
        if not rt.provenance_ok:
            issues.extend(rt.missing_fields)
        boundary_ok = True
        if record is not None:
            rec = self._runtime.check_record(record)
            if not rec.provenance_ok:
                issues.extend(rec.missing_fields)
            manifest = record.get("manifest") or record
            pv = self._boundary.validate_manifest(manifest)
            boundary_ok = pv.valid
            if not boundary_ok:
                issues.append("provenance_boundary_exceeded")
        return RuntimeProvenanceValidation(
            valid=len(issues) == 0,
            runtime_ok=rt.provenance_ok,
            boundary_ok=boundary_ok,
            issues=issues,
        )
