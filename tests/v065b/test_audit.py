"""Area 0: v065b audit artifacts."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "v065b" / "audit"


def test_external_skill_inventory() -> None:
    p = AUDIT / "external_skill_inventory.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["version"] == "0.6.5b"
    assert data["mounted_skills"][0]["skill_id"] == "karpathy_guidelines"


def test_audit_reports_exist() -> None:
    assert (AUDIT / "doctrine_conflict_report.md").is_file()
    assert (AUDIT / "constitutional_compatibility_matrix.md").is_file()
    assert (AUDIT / "guardian_risk_assessment.md").is_file()
