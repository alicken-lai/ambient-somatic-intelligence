#!/usr/bin/env python3
"""Validate Hermes canonical rules substrate (manifest + file presence)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = Path(__file__).resolve().parent
MANIFEST = RULES_DIR / "rule_manifest.json"
CANONICAL = RULES_DIR / "canonical_rules.md"
AGENTS = REPO_ROOT / "AGENTS.md"


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if not MANIFEST.is_file():
        _fail(f"missing manifest: {MANIFEST}")
    if not CANONICAL.is_file():
        _fail(f"missing canonical: {CANONICAL}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    generated = manifest.get("generated_files", {})
    if not generated:
        _fail("manifest has empty generated_files")

    missing: list[str] = []
    for _ide, rel in generated.items():
        path = REPO_ROOT / rel
        if not path.is_file():
            missing.append(rel)
    if missing:
        _fail("missing generated files: " + ", ".join(missing))

    canonical_src = manifest.get("canonical_source", "")
    if canonical_src != "hermes/rules/canonical_rules.md":
        _fail(f"unexpected canonical_source: {canonical_src!r}")

    canonical_text = CANONICAL.read_text(encoding="utf-8")
    if "canonical_version: 1.0.0" not in canonical_text:
        _fail("canonical_rules.md missing canonical_version: 1.0.0")

    agents_text = AGENTS.read_text(encoding="utf-8")
    if "hermes/rules/canonical_rules.md" not in agents_text:
        _fail("AGENTS.md does not reference hermes/rules/canonical_rules.md")

    if not re.search(r"canonical_rules\.md", agents_text):
        _fail("AGENTS.md missing canonical_rules.md reference")

    print("OK: hermes rules substrate valid")
    print(f"  version={manifest.get('version')}")
    print(f"  files_checked={len(generated)}")


if __name__ == "__main__":
    main()
