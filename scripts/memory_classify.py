"""
Memory Classification Engine — Phase 0 of Memory Architecture Refactor.

Classifies DMN records into layered memory stores:
  episodic/   — task history, execution traces, failures, debugging sessions
  semantic/   — repo knowledge, architecture decisions, stable concepts
  procedural/ — successful workflows, reusable plans, tool sequences
  governance/ — blocked actions, unsafe attempts, policy decisions, incidents
  scratchpad/ — telemetry ticks, transient state (auto-TTL candidates)
  archive/    — cold data, superseded records

Reads from memory/dmn.jsonl, writes classified records to memory/<layer>/records.jsonl.
Original dmn.jsonl is NOT modified (append-only contract preserved).
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
MEMORY_DIR = AMBIENT_ROOT / "memory"
DMN_PATH = MEMORY_DIR / "dmn.jsonl"

LAYERS = ["episodic", "semantic", "procedural", "governance", "scratchpad", "archive"]

GOVERNANCE_SIGNALS = {
    "guardian", "approval", "blocked", "block", "incident", "security",
    "reflex", "policy", "unsafe", "violation", "risk",
}

SEMANTIC_SIGNALS = {
    "architecture", "design", "schema", "protocol", "concept", "principle",
    "identity", "manifesto", "core_values", "public-architecture",
    "release", "milestone",
}

PROCEDURAL_SIGNALS = {
    "workflow", "setup", "config", "install", "migration", "procedure",
    "deploy", "build", "recipe", "howto", "fix", "resolved", "solution",
    "cursor", "mcp", "hermes",
}

EPISODIC_SIGNALS = {
    "night", "debug", "diagnosis", "recovery", "issue", "error",
    "failure", "trace", "session", "investigation", "audit",
}

SCRATCHPAD_SOURCES = {
    "night35-dmn-tick", "dmn-tick", "sense_local", "dmn_tick_loop",
}


def classify_record(record: dict[str, Any]) -> str:
    """Classify a single DMN record into a memory layer."""
    source = record.get("source", "").lower()
    tags = {t.lower() for t in record.get("tags", [])}
    content = record.get("content", "")

    content_lower = content.lower() if isinstance(content, str) else str(content).lower()

    if source in SCRATCHPAD_SOURCES or "autonomous_dmn_tick" in content_lower:
        return "scratchpad"

    all_signals = tags | {source}

    if all_signals & GOVERNANCE_SIGNALS:
        return "governance"

    if all_signals & PROCEDURAL_SIGNALS:
        if any(kw in content_lower for kw in ("設定", "解決", "安裝", "config", "setup", "fix", "resolved")):
            return "procedural"
        return "episodic"

    if all_signals & SEMANTIC_SIGNALS:
        return "semantic"

    if all_signals & EPISODIC_SIGNALS:
        return "episodic"

    if "cursor-agent" in source:
        return "procedural"

    if len(content) < 100 and not tags:
        return "scratchpad"

    return "episodic"


def run_classification(dry_run: bool = False) -> dict[str, int]:
    """Classify all DMN records and write to layer files."""
    if not DMN_PATH.exists():
        print(f"DMN file not found: {DMN_PATH}", file=sys.stderr)
        return {}

    counts: Counter[str] = Counter()
    layer_records: dict[str, list[dict]] = {layer: [] for layer in LAYERS}

    with open(DMN_PATH, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print(f"  Skipping malformed line {line_num}", file=sys.stderr)
                continue

            layer = classify_record(record)
            record["_classified_layer"] = layer
            record["_source_line"] = line_num
            layer_records[layer].append(record)
            counts[layer] += 1

    total = sum(counts.values())
    print(f"\n=== Memory Classification Report ===")
    print(f"Total records: {total}")
    print(f"{'Layer':<15} {'Count':>6} {'Pct':>7}")
    print("-" * 30)
    for layer in LAYERS:
        c = counts.get(layer, 0)
        pct = (c / total * 100) if total else 0
        print(f"{layer:<15} {c:>6} {pct:>6.1f}%")

    if dry_run:
        print("\n[DRY RUN] No files written.")
        return dict(counts)

    for layer in LAYERS:
        layer_dir = MEMORY_DIR / layer
        layer_dir.mkdir(parents=True, exist_ok=True)
        out_path = layer_dir / "records.jsonl"
        with open(out_path, "w", encoding="utf-8") as f:
            for rec in layer_records[layer]:
                f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
        if layer_records[layer]:
            print(f"  Wrote {len(layer_records[layer])} records to {out_path}")

    return dict(counts)


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    run_classification(dry_run=dry)
