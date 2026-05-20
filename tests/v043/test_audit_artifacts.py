"""Area 9 — Phase 0 audit artifacts exist."""

from __future__ import annotations

import json
from pathlib import Path


def test_v043_audit_files_present() -> None:
    audit = Path(__file__).resolve().parents[2] / "v043" / "audit"
    assert (audit / "execution_authority_audit.json").is_file()
    assert (audit / "mutation_surface_report.md").is_file()
    assert (audit / "write_target_inventory.json").is_file()
    assert (audit / "callback_authority_report.md").is_file()

    data = json.loads((audit / "execution_authority_audit.json").read_text())
    assert data["version"] == "0.4.3"
    assert data["total_scanned_mutations"] > 0
