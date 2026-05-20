"""Registry for mounted external skills — read-only advisory path."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from governance.external.constitutional_adapter import ConstitutionalAdapter
from governance.external.contamination_guard import ContaminationGuard
from governance.external.doctrine_drift_detector import DoctrineDriftDetector
from governance.external.provenance_boundary import ProvenanceBoundary
from hermes.skills.external.external_skill_record import ExternalSkillRecord
from hermes.skills.external.external_skill_status import ExternalSkillStatus

_REPO = Path(__file__).resolve().parents[3]
_DEFAULT_MOUNT = _REPO / "hermes" / "skills" / "external" / "karpathy_guidelines"


class ExternalSkillRegistry:
    """
    Mount pipeline: IMPORTED → FILTERED → COMPATIBLE | RESTRICTED | BLOCKED.

    Never overrides CognitiveGovernor acceptance; advisory hints only.
    """

    def __init__(self) -> None:
        self.adapter = ConstitutionalAdapter()
        self.contamination = ContaminationGuard()
        self.drift = DoctrineDriftDetector()
        self.provenance = ProvenanceBoundary()
        self._records: dict[str, ExternalSkillRecord] = {}

    def mount_from_directory(
        self,
        skill_id: str,
        mount_dir: Path,
        *,
        name: str,
        source_url: str,
        source_commit: str = "main",
    ) -> ExternalSkillRecord:
        skill_path = mount_dir / "SKILL.md"
        text = skill_path.read_text(encoding="utf-8") if skill_path.is_file() else ""
        record = ExternalSkillRecord(
            skill_id=skill_id,
            name=name,
            source_url=source_url,
            source_commit=source_commit,
            status=ExternalSkillStatus.IMPORTED,
            mount_path=str(mount_dir),
        )
        self._records[skill_id] = record

        prov = self.provenance.validate_mount_dir(mount_dir)
        record.provenance_hash = prov.content_hash

        filtered = self.adapter.filter.filter(text)
        record.status = ExternalSkillStatus.FILTERED
        record.filter_notes = list(filtered.violations)

        contam = self.contamination.scan(text)
        if contam.contaminated:
            record.filter_notes.extend(contam.signals)

        adapt = self.adapter.adapt(text, metadata={"skill_id": skill_id})
        record.compatibility_score = adapt.compliance_score

        drift = self.drift.compare(text)
        if drift.drift_detected:
            record.filter_notes.append("doctrine_drift")

        if not prov.valid or "sovereign_truth_rejected" in adapt.notes:
            record.status = ExternalSkillStatus.BLOCKED
        elif filtered.violations or contam.contaminated:
            record.status = ExternalSkillStatus.RESTRICTED
        elif adapt.compatible:
            record.status = ExternalSkillStatus.COMPATIBLE
        else:
            record.status = ExternalSkillStatus.RESTRICTED

        return record

    def register_default_karpathy(self) -> ExternalSkillRecord:
        return self.mount_from_directory(
            "karpathy_guidelines",
            _DEFAULT_MOUNT,
            name="karpathy-guidelines",
            source_url="https://github.com/multica-ai/andrej-karpathy-skills",
            source_commit="main",
        )

    def get(self, skill_id: str) -> ExternalSkillRecord | None:
        return self._records.get(skill_id)

    def list_records(self) -> list[ExternalSkillRecord]:
        return list(self._records.values())

    def advisory_for_route(self, route_name: str) -> dict[str, Any]:
        """Read-only advisory bundle — never changes governance decisions."""
        if not self._records:
            self.register_default_karpathy()
        hints: list[str] = []
        statuses: list[str] = []
        for rec in self._records.values():
            statuses.append(rec.status.value)
            if rec.status.is_advisory_allowed():
                hints.append(f"{rec.name}:advisory_ok")
            elif rec.status.is_blocked():
                hints.append(f"{rec.name}:blocked_do_not_apply")
        return {
            "route_name": route_name,
            "advisory_only": True,
            "constitutional_supremacy": True,
            "skill_statuses": statuses,
            "hints": hints,
            "disclaimer": "external_skill_advisory_not_sovereign",
        }

    def load_inventory(self, path: Path) -> dict[str, Any]:
        if not path.is_file():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
