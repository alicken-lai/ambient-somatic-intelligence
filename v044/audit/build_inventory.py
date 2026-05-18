#!/usr/bin/env python3
"""Build v0.4.4 legacy mutation inventory from v0.4.3 execution authority audit."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
V043_AUDIT = REPO_ROOT / "v043" / "audit" / "execution_authority_audit.json"
OUT_DIR = Path(__file__).resolve().parent

CALLBACK_HINTS = re.compile(
    r"callback|hook|subscribe|signal_bus|\.on\(|register_guarded|integration_bus",
    re.I,
)
REGISTRY_HINTS = re.compile(
    r"registry|skill_registry|patch_registry|truth_registry|register_skill|deregister",
    re.I,
)
SINGLETON_HINTS = re.compile(
    r"singleton|_instance|get_instance|global_registry|_global_",
    re.I,
)
FILE_PATTERNS = frozenset({"append", "open_write", "write_text", "shutil"})

CRITICAL_TARGETS = frozenset({
    "governance_audit",
    "memory",
    "memory/dmn.jsonl",
    "skill_registry",
    "truth_graph",
    "state",
    "state/checkpoint",
})


def _authority_model(entry: dict) -> str:
    mech = entry.get("permission_mechanism", "implicit")
    if mech == "explicit":
        return "execution_context"
    if entry.get("write_target") in CRITICAL_TARGETS:
        return "implicit_high_risk"
    return "implicit_legacy"


def _rollback_coverage(entry: dict) -> str:
    rb = entry.get("rollback_mechanism", "none")
    if rb and rb != "none":
        return rb
    wt = entry.get("write_target", "unknown")
    if wt in CRITICAL_TARGETS or entry.get("risk_level") == "high":
        return "missing_required"
    return "none"


def _complexity(category: str, entry: dict) -> str:
    if entry.get("risk_level") == "high":
        return "high"
    if category in ("REGISTRY_MUTATION", "CALLBACK_MUTATION"):
        return "medium"
    if category == "FILE_WRITE" and entry.get("write_target") in CRITICAL_TARGETS:
        return "medium"
    return "low"


def _risk_score(entry: dict, category: str) -> float:
    base = {"high": 0.9, "medium": 0.5, "low": 0.2}.get(entry.get("risk_level", "medium"), 0.5)
    if category == "UNKNOWN":
        base += 0.15
    if entry.get("write_target") in CRITICAL_TARGETS:
        base += 0.1
    if _rollback_coverage(entry) == "missing_required":
        base += 0.1
    return min(1.0, round(base, 3))


def classify(entry: dict) -> str:
    path = entry.get("path", "")
    pattern = entry.get("pattern", "")
    wt = str(entry.get("write_target", "unknown"))

    if CALLBACK_HINTS.search(path):
        return "CALLBACK_MUTATION"
    if REGISTRY_HINTS.search(path) or wt in ("skill_registry", "truth_graph"):
        return "REGISTRY_MUTATION"
    if SINGLETON_HINTS.search(path):
        return "SINGLETON_MUTATION"
    if pattern in FILE_PATTERNS or "write" in pattern:
        return "FILE_WRITE"
    return "UNKNOWN"


def enrich(entry: dict) -> dict:
    category = classify(entry)
    return {
        **entry,
        "category": category,
        "current_authority_model": _authority_model(entry),
        "rollback_coverage": _rollback_coverage(entry),
        "migration_complexity": _complexity(category, entry),
        "risk_score": _risk_score(entry, category),
        "migrated": False,
        "migration_guard": None,
    }


def build_report_md(inventory: dict) -> str:
    by_cat = Counter(e["category"] for e in inventory["entries"])
    by_risk = Counter(e["risk_level"] for e in inventory["entries"])
    lines = [
        "# Mutation Classification Report (v0.4.4)",
        "",
        f"**Generated:** {inventory['generated_at']}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Source audit version | {inventory['source_version']} |",
        f"| Total scanned (v043 metadata) | {inventory['total_scanned_mutations']} |",
        f"| Catalogued paths (detail) | {inventory['catalogued_paths']} |",
        f"| High risk | {by_risk.get('high', 0)} |",
        "",
        "## By Category",
        "",
        "| Category | Count |",
        "|----------|-------|",
    ]
    for cat in (
        "FILE_WRITE",
        "SINGLETON_MUTATION",
        "CALLBACK_MUTATION",
        "REGISTRY_MUTATION",
        "UNKNOWN",
    ):
        lines.append(f"| {cat} | {by_cat.get(cat, 0)} |")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Classification is heuristic from path/pattern/write_target.",
            "- `total_scanned_mutations` from v043 may exceed catalogued detail rows.",
            "- Migration status starts `migrated=false`; coverage scanner updates counts.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    data = json.loads(V043_AUDIT.read_text(encoding="utf-8"))
    entries = [enrich(e) for e in data.get("mutation_paths", [])]
    inventory = {
        "version": "0.4.4",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_version": data.get("version", "0.4.3"),
        "source_audit": str(V043_AUDIT.relative_to(REPO_ROOT)),
        "total_scanned_mutations": data.get("total_scanned_mutations", len(entries)),
        "catalogued_paths": len(entries),
        "entries": entries,
        "by_category": dict(Counter(e["category"] for e in entries)),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    inv_path = OUT_DIR / "legacy_mutation_inventory.json"
    inv_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT_DIR / "mutation_classification_report.md").write_text(
        build_report_md(inventory), encoding="utf-8"
    )
    print(f"wrote {inv_path} ({len(entries)} entries)")


if __name__ == "__main__":
    main()
