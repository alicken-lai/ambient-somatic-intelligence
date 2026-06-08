"""Tests for the Phase B (section 9.4) agent-memory migration script.

Verifies non-destructive behavior: dry-run writes nothing, apply writes a new
file + audit and never overwrites the original, and the Phase 1E corrections
land on the right entries.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "migrate_agent_memory_layers.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("migrate_agent_memory_layers", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclasses (with `from __future__ import
    # annotations`) can resolve annotations via sys.modules[__module__].
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


mig = _load_module()


LEGACY_ENTRIES = [
    # FE-STRAT-001: should demote to L2 + confidence 0.3
    {"content": "Tailwind @apply for repeated component styles reduces class duplication",
     "category": "strategy", "confidence": 1.0, "uses": 0},
    # FE-STRAT-002: should demote to L2 + confidence 0.3
    {"content": "Use React.lazy + Suspense for code splitting large pages",
     "category": "strategy", "confidence": 1.0, "uses": 0},
    # FE-KNOW-001: confidence -> 0.6
    {"content": "React useCallback prevents unnecessary re-renders",
     "category": "knowledge", "confidence": 1.0, "uses": 0},
    # untouched-by-correction knowledge (still gets schema backfill)
    {"content": "Some neutral fact about CSS grid",
     "category": "knowledge", "confidence": 0.4, "uses": 2},
]


@pytest.fixture
def root(tmp_path: Path) -> Path:
    mem_dir = tmp_path / "state" / "agents" / "frontend-agent" / "memory"
    mem_dir.mkdir(parents=True)
    entries = mem_dir / "entries.jsonl"
    entries.write_text(
        "\n".join(json.dumps(e) for e in LEGACY_ENTRIES) + "\n",
        encoding="utf-8",
    )
    return tmp_path


def test_dry_run_writes_nothing(root: Path):
    entries = root / "state" / "agents" / "frontend-agent" / "memory" / "entries.jsonl"
    before = entries.read_text(encoding="utf-8")

    report = mig.migrate(root, dry_run=True)

    assert report.dry_run is True
    assert report.total_changes > 0
    assert report.audit_file is None
    # original untouched, no migrated file, no audit dir
    assert entries.read_text(encoding="utf-8") == before
    assert not (entries.with_name("entries.migrated.jsonl")).exists()
    assert not (root / "observability" / "evolution_audit").exists()


def test_apply_writes_new_file_and_audit_without_overwrite(root: Path):
    entries = root / "state" / "agents" / "frontend-agent" / "memory" / "entries.jsonl"
    before = entries.read_text(encoding="utf-8")

    report = mig.migrate(root, dry_run=False)

    # original preserved
    assert entries.read_text(encoding="utf-8") == before
    # new file created
    out = entries.with_name("entries.migrated.jsonl")
    assert out.exists()
    # audit record created
    assert report.audit_file is not None
    assert Path(report.audit_file).exists()
    audit = json.loads(Path(report.audit_file).read_text(encoding="utf-8"))
    assert audit["dry_run"] is False
    assert audit["total_changes"] == report.total_changes


def test_corrections_applied_in_migrated_output(root: Path):
    entries = root / "state" / "agents" / "frontend-agent" / "memory" / "entries.jsonl"
    mig.migrate(root, dry_run=False)
    rows = [json.loads(line) for line in
            entries.with_name("entries.migrated.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()]
    by_content = {r["content"]: r for r in rows}

    strat1 = by_content["Tailwind @apply for repeated component styles reduces class duplication"]
    assert strat1["layer"] == 2
    assert strat1["confidence"] == 0.3

    strat2 = by_content["Use React.lazy + Suspense for code splitting large pages"]
    assert strat2["layer"] == 2
    assert strat2["confidence"] == 0.3

    know1 = by_content["React useCallback prevents unnecessary re-renders"]
    assert know1["confidence"] == 0.6
    assert know1["layer"] == 1

    neutral = by_content["Some neutral fact about CSS grid"]
    assert neutral["confidence"] == 0.4  # unchanged value
    # but schema backfilled
    assert "entry_id" in neutral
    assert "success_count" in neutral
    assert "contexts_validated" in neutral


def test_schema_backfill_recorded_for_every_entry(root: Path):
    report = mig.migrate(root, dry_run=True)
    agent = report.agents[0]
    assert agent.total_entries == len(LEGACY_ENTRIES)
    # each legacy entry lacked 5 schema fields -> 5 backfill changes minimum
    backfills = [c for c in agent.changes if c.reason.startswith("backfill")]
    assert len(backfills) == len(LEGACY_ENTRIES) * 5


def test_no_agents_dir_is_safe(tmp_path: Path):
    report = mig.migrate(tmp_path, dry_run=True)
    assert report.agents == []
    assert report.total_changes == 0
