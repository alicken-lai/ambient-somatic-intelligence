"""Migrate agent memory entries to the ontology-aligned schema (Phase B, section 9.4).

Backfills the Phase A/B schema fields (layer / entry_id / success_count /
failure_count / contexts_validated) and applies the Phase 1E false-strategy
corrections (see replay/reports/false_strategy_report.md).

Non-destructive by design:
  - dry-run by default (computes a report, writes nothing);
  - when applied, writes a NEW file (entries.migrated.jsonl) plus an append-only
    audit record under observability/evolution_audit/, and never overwrites the
    original entries.jsonl.

Usage:
    python scripts/migrate_agent_memory_layers.py            # dry-run
    python scripts/migrate_agent_memory_layers.py --apply    # write migrated file + audit
    python scripts/migrate_agent_memory_layers.py --root /path/to/ambient-os
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.memory import MemoryEntry


# (required_substrings, changes, reason). A correction applies when every
# substring is present (case-insensitive) in the entry content.
CONTENT_CORRECTIONS: list[tuple[list[str], dict[str, Any], str]] = [
    (["tailwind", "@apply"], {"layer": 2, "confidence": 0.3},
     "FE-STRAT-001 false strategy: demote to L2, confidence 0.3"),
    (["react.lazy"], {"layer": 2, "confidence": 0.3},
     "FE-STRAT-002 false strategy: demote to L2, confidence 0.3"),
    (["code splitting"], {"layer": 2, "confidence": 0.3},
     "FE-STRAT-002 false strategy: demote to L2, confidence 0.3"),
    (["inline styles"], {"confidence": 0.5},
     "FE-FAIL-001 overconfident: confidence 0.5"),
    (["usecallback"], {"confidence": 0.6},
     "FE-KNOW-001 overconfident: confidence 0.6"),
    (["composition", "inheritance"], {"confidence": 0.6},
     "FE-KNOW-002 overconfident: confidence 0.6"),
]


@dataclass
class EntryChange:
    entry_id: str
    field_name: str
    old: Any
    new: Any
    reason: str


@dataclass
class AgentMigration:
    agent_id: str
    source: str
    total_entries: int = 0
    changes: list[EntryChange] = field(default_factory=list)
    output_file: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "source": self.source,
            "total_entries": self.total_entries,
            "change_count": len(self.changes),
            "changes": [vars(c) for c in self.changes],
            "output_file": self.output_file,
        }


@dataclass
class MigrationReport:
    dry_run: bool
    root: str
    agents: list[AgentMigration] = field(default_factory=list)
    audit_file: str | None = None

    @property
    def total_changes(self) -> int:
        return sum(len(a.changes) for a in self.agents)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dry_run": self.dry_run,
            "root": self.root,
            "generated": datetime.now(tz=timezone.utc).isoformat(),
            "total_changes": self.total_changes,
            "agents": [a.to_dict() for a in self.agents],
            "audit_file": self.audit_file,
        }


def _default_root() -> Path:
    return Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))


def _correction_for(content: str) -> tuple[dict[str, Any], str] | None:
    low = content.lower()
    for subs, changes, reason in CONTENT_CORRECTIONS:
        if all(s in low for s in subs):
            return changes, reason
    return None


def migrate_entry(raw: dict[str, Any]) -> tuple[dict[str, Any], list[EntryChange]]:
    """Return (migrated_row, changes) for one raw entry dict. Pure / no I/O."""
    changes: list[EntryChange] = []
    had = {
        "layer": "layer" in raw,
        "entry_id": bool(raw.get("entry_id")),
        "success_count": "success_count" in raw,
        "failure_count": "failure_count" in raw,
        "contexts_validated": "contexts_validated" in raw,
    }

    entry = MemoryEntry.from_dict(raw)  # backfills missing schema fields
    eid = entry.entry_id

    if not had["layer"]:
        changes.append(EntryChange(eid, "layer", None, entry.layer, "backfill: layer from category"))
    if not had["entry_id"]:
        changes.append(EntryChange(eid, "entry_id", None, eid, "backfill: generated entry_id"))
    if not had["success_count"]:
        changes.append(EntryChange(eid, "success_count", None, 0, "backfill"))
    if not had["failure_count"]:
        changes.append(EntryChange(eid, "failure_count", None, 0, "backfill"))
    if not had["contexts_validated"]:
        changes.append(EntryChange(eid, "contexts_validated", None, [], "backfill"))

    correction = _correction_for(entry.content)
    if correction is not None:
        change_map, reason = correction
        if "layer" in change_map and entry.layer > change_map["layer"]:
            changes.append(EntryChange(eid, "layer", entry.layer, change_map["layer"], reason))
            entry.layer = change_map["layer"]
        if "confidence" in change_map and entry.confidence > change_map["confidence"]:
            target = change_map["confidence"]
            changes.append(EntryChange(eid, "confidence", entry.confidence, target, reason))
            entry.confidence = target

    return entry.to_dict(), changes


def migrate(root: Path | str | None = None, *, dry_run: bool = True) -> MigrationReport:
    """Scan state/agents/*/memory/entries.jsonl and migrate the schema.

    Returns a MigrationReport. With dry_run=True (default) nothing is written.
    """
    root_path = Path(root) if root is not None else _default_root()
    agents_dir = root_path / "state" / "agents"
    report = MigrationReport(dry_run=dry_run, root=str(root_path))

    if not agents_dir.is_dir():
        return report

    for agent_path in sorted(agents_dir.iterdir()):
        entries_file = agent_path / "memory" / "entries.jsonl"
        if not entries_file.is_file():
            continue

        agent_mig = AgentMigration(agent_id=agent_path.name, source=str(entries_file))
        migrated_rows: list[dict[str, Any]] = []

        for line in entries_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            agent_mig.total_entries += 1
            new_row, changes = migrate_entry(raw)
            migrated_rows.append(new_row)
            agent_mig.changes.extend(changes)

        if not dry_run:
            out_file = entries_file.with_name("entries.migrated.jsonl")
            out_file.write_text(
                "\n".join(json.dumps(r) for r in migrated_rows) + "\n",
                encoding="utf-8",
            )
            agent_mig.output_file = str(out_file)

        report.agents.append(agent_mig)

    if not dry_run:
        audit_dir = root_path / "observability" / "evolution_audit"
        audit_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        audit_file = audit_dir / f"agent_memory_migration_{stamp}.json"
        audit_file.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        report.audit_file = str(audit_file)

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Migrate agent memory to the ontology schema (Phase B 9.4)."
    )
    parser.add_argument("--root", default=None,
                        help="Ambient OS root (defaults to AMBIENT_OS_ROOT).")
    parser.add_argument("--apply", action="store_true",
                        help="Apply migration (default is dry-run).")
    args = parser.parse_args(argv)

    report = migrate(args.root, dry_run=not args.apply)
    print(json.dumps(report.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
