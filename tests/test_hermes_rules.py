"""Tests for Hermes canonical rules substrate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = REPO_ROOT / "hermes" / "rules"


def test_manifest_exists_and_lists_files():
    manifest_path = RULES_DIR / "rule_manifest.json"
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["canonical_source"] == "hermes/rules/canonical_rules.md"
    assert manifest["version"] == "1.0.0"
    for rel in manifest["generated_files"].values():
        assert (REPO_ROOT / rel).is_file(), f"missing: {rel}"


def test_canonical_exists():
    canonical = RULES_DIR / "canonical_rules.md"
    assert canonical.is_file()
    text = canonical.read_text(encoding="utf-8")
    assert "canonical_version: 1.0.0" in text
    assert "## 1. Constitution" in text


def test_agents_references_canonical():
    agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "hermes/rules/canonical_rules.md" in agents


def test_validate_rules_script_exits_zero():
    script = RULES_DIR / "validate_rules.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
