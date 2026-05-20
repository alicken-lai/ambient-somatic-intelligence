"""Area 1: Karpathy skill mount + provenance."""

import json
from pathlib import Path

MOUNT = Path(__file__).resolve().parents[2] / "hermes" / "skills" / "external" / "karpathy_guidelines"


def test_skill_and_manifest() -> None:
    assert (MOUNT / "SKILL.md").is_file()
    manifest = json.loads((MOUNT / "source_manifest.json").read_text(encoding="utf-8"))
    assert manifest["advisory_only"] is True
    assert "multica-ai" in manifest["source_url"]


def test_provenance_record() -> None:
    record = json.loads((MOUNT / "provenance_record.json").read_text(encoding="utf-8"))
    assert record["governance"]["constitutional_supremacy"] is True
