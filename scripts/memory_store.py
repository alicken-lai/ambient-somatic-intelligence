"""
Layered Memory Store — Phase 1 of Memory Architecture Refactor.

Provides a unified API for writing to and reading from the layered memory system.
Replaces direct dmn.jsonl append with layer-aware writes that:
  1. Classify the record into the appropriate memory layer
  2. Write to the layer-specific store
  3. Update the inverted index
  4. Optionally write to dmn.jsonl for backward compatibility

Layers:
  episodic/   — task history, execution traces, failures, debugging sessions
  semantic/   — repo knowledge, architecture decisions, stable concepts
  procedural/ — successful workflows, reusable plans, tool sequences
  governance/ — blocked actions, unsafe attempts, policy decisions, incidents
  scratchpad/ — telemetry ticks, transient state (auto-TTL candidates)
  archive/    — cold data, superseded records
"""

from __future__ import annotations

import json
import os
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from memory_classify import classify_record, LAYERS

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
MEMORY_DIR = AMBIENT_ROOT / "memory"
DMN_PATH = MEMORY_DIR / "dmn.jsonl"
INDEX_PATH = MEMORY_DIR / "index.json"

LAYER_PRIORITY = {
    "semantic": 1,
    "procedural": 2,
    "governance": 3,
    "episodic": 4,
    "scratchpad": 5,
    "archive": 6,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _load_index() -> dict[str, Any]:
    if INDEX_PATH.exists():
        try:
            return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"tags": {}, "hashes": {}, "stats": {"total": 0, "by_layer": {}}}


def _save_index(index: dict[str, Any]) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _update_index(index: dict[str, Any], record: dict[str, Any], layer: str, record_id: str) -> None:
    """Update the inverted index with the new record."""
    for tag in record.get("tags", []):
        tag_lower = tag.lower()
        if tag_lower not in index["tags"]:
            index["tags"][tag_lower] = []
        index["tags"][tag_lower].append({"layer": layer, "id": record_id, "ts": record.get("timestamp", "")})

    chash = content_hash(record.get("content", ""))
    index["hashes"][chash] = {"layer": layer, "id": record_id}

    index["stats"]["total"] += 1
    index["stats"]["by_layer"][layer] = index["stats"].get("by_layer", {}).get(layer, 0) + 1


def is_duplicate(content: str, index: dict[str, Any] | None = None) -> bool:
    """Check if content already exists in memory (by hash)."""
    if index is None:
        index = _load_index()
    chash = content_hash(content)
    return chash in index.get("hashes", {})


def store_memory(
    content: str,
    tags: list[str] | None = None,
    source: str = "manual",
    layer: str | None = None,
    skip_dmn: bool = False,
    skip_dedup: bool = False,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Store a memory record into the appropriate layer.

    Args:
        content: The memory content to store
        tags: List of tags for indexing and classification
        source: Source identifier (e.g., "cursor-agent", "night35-dmn-tick")
        layer: Force a specific layer (skips auto-classification if provided)
        skip_dmn: If True, don't write to dmn.jsonl (for migration use)
        skip_dedup: If True, don't check for duplicates
        metadata: Additional metadata to attach to the record

    Returns:
        Dict with record details and storage location
    """
    tags = tags or []
    now = utc_now()

    record = {
        "timestamp": now,
        "source": source,
        "tags": tags,
        "content": content,
    }
    if metadata:
        record["metadata"] = metadata

    index = _load_index()

    if not skip_dedup and is_duplicate(content, index):
        return {
            "status": "duplicate",
            "content_hash": content_hash(content),
            "message": "Record with identical content already exists",
        }

    if layer is None:
        layer = classify_record(record)

    if layer not in LAYERS:
        raise ValueError(f"Invalid layer: {layer}. Must be one of {LAYERS}")

    layer_dir = MEMORY_DIR / layer
    layer_dir.mkdir(parents=True, exist_ok=True)
    layer_file = layer_dir / "records.jsonl"

    record_id = f"{layer}:{content_hash(content)}:{now}"
    record["_id"] = record_id
    record["_layer"] = layer

    with layer_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    if not skip_dmn:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        dmn_record = {
            "timestamp": now,
            "source": source,
            "tags": tags,
            "content": content,
        }
        with DMN_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(dmn_record, ensure_ascii=False, sort_keys=True) + "\n")

    _update_index(index, record, layer, record_id)
    _save_index(index)

    return {
        "status": "stored",
        "layer": layer,
        "record_id": record_id,
        "timestamp": now,
        "content_hash": content_hash(content),
    }


def read_layer(
    layer: str,
    limit: int = 50,
    offset: int = 0,
    tags_filter: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Read records from a specific memory layer."""
    if layer not in LAYERS:
        raise ValueError(f"Invalid layer: {layer}. Must be one of {LAYERS}")

    layer_file = MEMORY_DIR / layer / "records.jsonl"
    if not layer_file.exists():
        return []

    records: list[dict[str, Any]] = []
    with layer_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            if tags_filter:
                record_tags = {t.lower() for t in record.get("tags", [])}
                if not any(t.lower() in record_tags for t in tags_filter):
                    continue

            records.append(record)

    records.reverse()
    return records[offset : offset + limit]


def layer_stats() -> dict[str, Any]:
    """Get statistics about all memory layers."""
    stats: dict[str, Any] = {"total": 0, "layers": {}}

    for layer in LAYERS:
        layer_file = MEMORY_DIR / layer / "records.jsonl"
        if not layer_file.exists():
            stats["layers"][layer] = {"count": 0, "size_bytes": 0}
            continue

        count = 0
        with layer_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1

        size = layer_file.stat().st_size
        stats["layers"][layer] = {"count": count, "size_bytes": size}
        stats["total"] += count

    dmn_count = 0
    if DMN_PATH.exists():
        with DMN_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    dmn_count += 1

    stats["dmn_total"] = dmn_count
    stats["dmn_size_bytes"] = DMN_PATH.stat().st_size if DMN_PATH.exists() else 0

    return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Layered Memory Store")
    sub = parser.add_subparsers(dest="cmd", required=True)

    store_p = sub.add_parser("store")
    store_p.add_argument("content")
    store_p.add_argument("--tag", action="append", default=[])
    store_p.add_argument("--source", default="manual")
    store_p.add_argument("--layer", choices=LAYERS, default=None)

    read_p = sub.add_parser("read")
    read_p.add_argument("layer", choices=LAYERS)
    read_p.add_argument("--limit", type=int, default=10)
    read_p.add_argument("--tag", action="append", default=[])

    sub.add_parser("stats")

    args = parser.parse_args()

    if args.cmd == "store":
        result = store_memory(args.content, args.tag, args.source, args.layer)
        print(json.dumps(result, indent=2))
    elif args.cmd == "read":
        records = read_layer(args.layer, limit=args.limit, tags_filter=args.tag or None)
        for r in records:
            print(json.dumps(r, ensure_ascii=False))
    else:
        print(json.dumps(layer_stats(), indent=2))
