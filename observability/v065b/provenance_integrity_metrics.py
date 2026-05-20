"""Provenance integrity metrics for external mounts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from governance.external.provenance_boundary import ProvenanceBoundary

_REPO = Path(__file__).resolve().parents[2]
_MOUNT = _REPO / "hermes" / "skills" / "external" / "karpathy_guidelines"


@dataclass
class ProvenanceIntegrityMetrics:
    integrity_rate: float = 1.0
    mount_valid: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "integrity_rate": round(self.integrity_rate, 4),
            "mount_valid": self.mount_valid,
        }


def collect_provenance_integrity_metrics() -> ProvenanceIntegrityMetrics:
    boundary = ProvenanceBoundary()
    verdict = boundary.validate_mount_dir(_MOUNT)
    return ProvenanceIntegrityMetrics(
        integrity_rate=1.0 if verdict.valid else 0.0,
        mount_valid=verdict.valid,
    )
