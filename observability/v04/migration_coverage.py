"""v0.4.4 migration coverage — scan repo vs legacy mutation inventory."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INVENTORY = REPO_ROOT / "v044" / "audit" / "legacy_mutation_inventory.json"

GUARD_MARKERS = {
    "FILE_WRITE": re.compile(
        r"GuardedFileWriter|guarded_file_writer|append_jsonl\(",
        re.I,
    ),
    "CALLBACK_MUTATION": re.compile(
        r"GuardedCallback|register_guarded_callback|CallbackGuard",
        re.I,
    ),
    "REGISTRY_MUTATION": re.compile(r"RegistryGuard|registry_guard\.mutate", re.I),
    "SINGLETON_MUTATION": re.compile(r"SingletonGuard|singleton_guard\.mutate", re.I),
}

MIGRATED_MODULES = frozenset({
    "governance/audit_log.py",
    "memory/memory_kernel.py",
    "skills/core/skill_registry.py",
    "somatic/signal_bus.py",
    "kernel/integration_bus.py",
    "kernel/isolation/governed_memory_writer.py",
    "kernel/wiring/patch_registry.py",
    "kernel/truth/truth_registry.py",
    "architecture/bus_decomposition/event_schema.py",
})

COVERAGE_GATE_THRESHOLD = 0.95


@dataclass
class CoverageReport:
    catalogued_paths: int = 0
    total_scanned_mutations: int = 0
    migrated_paths: int = 0
    coverage_ratio: float = 0.0
    by_category: dict[str, dict[str, Any]] = field(default_factory=dict)
    gate_pass: bool = False
    gate_threshold: float = COVERAGE_GATE_THRESHOLD
    honesty_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalogued_paths": self.catalogued_paths,
            "total_scanned_mutations": self.total_scanned_mutations,
            "migrated_paths": self.migrated_paths,
            "coverage_ratio": round(self.coverage_ratio, 4),
            "by_category": self.by_category,
            "gate_pass": self.gate_pass,
            "gate_threshold": self.gate_threshold,
            "honesty_note": self.honesty_note,
        }


def _load_inventory(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_has_guard(file_path: Path, category: str) -> bool:
    if not file_path.is_file():
        return False
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    pattern = GUARD_MARKERS.get(category)
    if pattern and pattern.search(text):
        return True
    rel = str(file_path.relative_to(REPO_ROOT)).replace("\\", "/")
    return rel in MIGRATED_MODULES


def _path_migrated(entry: dict, repo_root: Path) -> bool:
    if entry.get("migrated"):
        return True
    path_str = entry.get("path", "")
    if ":" not in path_str:
        return False
    rel, _line = path_str.split(":", 1)
    file_path = repo_root / rel
    return _file_has_guard(file_path, entry.get("category", "UNKNOWN"))


def compute_migration_coverage(
    inventory_path: Path | None = None,
    *,
    repo_root: Path | None = None,
) -> CoverageReport:
    root = repo_root or REPO_ROOT
    inv_path = inventory_path or DEFAULT_INVENTORY
    inventory = _load_inventory(inv_path)
    entries = inventory.get("entries", [])

    by_cat: dict[str, list[bool]] = {}
    migrated = 0
    for entry in entries:
        cat = entry.get("category", "UNKNOWN")
        is_mig = _path_migrated(entry, root)
        by_cat.setdefault(cat, []).append(is_mig)
        if is_mig:
            migrated += 1

    catalogued = len(entries)
    ratio = migrated / catalogued if catalogued else 0.0
    scanned = int(inventory.get("total_scanned_mutations", catalogued))

    cat_summary: dict[str, dict[str, Any]] = {}
    for cat, flags in by_cat.items():
        total = len(flags)
        mig = sum(1 for f in flags if f)
        cat_summary[cat] = {
            "total": total,
            "migrated": mig,
            "coverage": round(mig / total, 4) if total else 0.0,
        }

    note = ""
    if scanned > catalogued:
        note = (
            f"v043 audit reports {scanned} scanned mutations but only {catalogued} "
            "catalogued in detail; coverage is computed on catalogued paths."
        )

    return CoverageReport(
        catalogued_paths=catalogued,
        total_scanned_mutations=scanned,
        migrated_paths=migrated,
        coverage_ratio=ratio,
        by_category=cat_summary,
        gate_pass=ratio >= COVERAGE_GATE_THRESHOLD,
        honesty_note=note,
    )
