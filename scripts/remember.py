#!/usr/bin/env python3
"""Append-only DMN memory helper."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, record_checksum


ROOT = Path(__file__).resolve().parents[1]
MEMORY_FILE = ROOT / "memory" / "dmn.jsonl"
SCHEMA_FILE = ROOT / "memory" / "schema.json"


def validate_memory_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = {"timestamp", "source", "tags", "content"}
    extra = set(record) - expected
    missing = expected - set(record)
    if missing:
        errors.append(f"missing fields: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"unexpected fields: {', '.join(sorted(extra))}")
    if not isinstance(record.get("timestamp"), str) or not record.get("timestamp"):
        errors.append("timestamp must be a non-empty string")
    if not isinstance(record.get("source"), str) or not record.get("source"):
        errors.append("source must be a non-empty string")
    if not isinstance(record.get("content"), str) or not record.get("content"):
        errors.append("content must be a non-empty string")
    tags = record.get("tags")
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        errors.append("tags must be a list of strings")
    try:
        datetime.fromisoformat(str(record.get("timestamp")))
    except ValueError:
        errors.append("timestamp must be ISO-8601")
    return errors


def append_memory(content: str, tags: list[str] | None = None, source: str = "manual") -> dict[str, Any]:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "tags": tags or [],
        "content": content,
    }
    errors = validate_memory_record(record)
    if errors:
        raise ValueError("; ".join(errors))
    with MEMORY_FILE.open("a", encoding="utf-8") as memory:
        memory.write(json.dumps(record, sort_keys=True) + "\n")
    record_checksum(MEMORY_FILE, "dmn_memory_append", {"source": source, "tags": tags or []})
    log_action("memory:append", "completed", "ALLOW", {"source": source, "tags": tags or []})
    return record


def search_memory(query: str, limit: int = 20) -> list[dict[str, Any]]:
    if not MEMORY_FILE.exists():
        return []

    matches: list[dict[str, Any]] = []
    needle = query.casefold()
    with MEMORY_FILE.open("r", encoding="utf-8") as memory:
        for line in memory:
            if not line.strip():
                continue
            record = json.loads(line)
            haystack = json.dumps(record, sort_keys=True).casefold()
            if needle in haystack:
                matches.append(record)
    log_action("memory:search", "completed", "ALLOW", {"query": query, "matches": len(matches)})
    return matches[-limit:]


def validate_memory_file() -> dict[str, Any]:
    if not MEMORY_FILE.exists():
        return {"ok": True, "records": 0, "errors": []}

    errors: list[dict[str, Any]] = []
    records = 0
    with MEMORY_FILE.open("r", encoding="utf-8") as memory:
        for line_number, line in enumerate(memory, start=1):
            if not line.strip():
                continue
            records += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append({"line": line_number, "errors": [str(exc)]})
                continue
            record_errors = validate_memory_record(record)
            if record_errors:
                errors.append({"line": line_number, "errors": record_errors})
    result = {"ok": not errors, "records": records, "errors": errors, "schema": str(SCHEMA_FILE.relative_to(ROOT))}
    log_action("memory:validate", "completed" if result["ok"] else "failed", "ALLOW", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Append and search DMN memory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    append_parser = subparsers.add_parser("append")
    append_parser.add_argument("content")
    append_parser.add_argument("--tag", action="append", default=[])
    append_parser.add_argument("--source", default="manual")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=20)

    subparsers.add_parser("validate")

    args = parser.parse_args()
    if args.command == "append":
        print(json.dumps(append_memory(args.content, args.tag, args.source), sort_keys=True))
        return 0

    if args.command == "search":
        for record in search_memory(args.query, args.limit):
            print(json.dumps(record, sort_keys=True))
        return 0

    result = validate_memory_file()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
