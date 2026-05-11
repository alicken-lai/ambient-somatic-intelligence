#!/usr/bin/env python3
"""Append-only DMN memory helper."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MEMORY_FILE = ROOT / "memory" / "dmn.jsonl"


def append_memory(content: str, tags: list[str] | None = None, source: str = "manual") -> dict[str, Any]:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "tags": tags or [],
        "content": content,
    }
    with MEMORY_FILE.open("a", encoding="utf-8") as memory:
        memory.write(json.dumps(record, sort_keys=True) + "\n")
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
    return matches[-limit:]


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

    args = parser.parse_args()
    if args.command == "append":
        print(json.dumps(append_memory(args.content, args.tag, args.source), sort_keys=True))
        return 0

    for record in search_memory(args.query, args.limit):
        print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

