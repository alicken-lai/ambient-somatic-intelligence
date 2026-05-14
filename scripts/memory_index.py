"""
Memory Inverted Index — Phase 1 of Memory Architecture Refactor.

Builds and maintains an inverted index over all memory layers for fast retrieval.
Replaces linear-scan search with O(1) tag lookup and pre-scored relevance.

Index structure:
  memory/index.json — tag→records mapping, content hashes, layer stats
  memory/trigram_index.json — trigram→records for fuzzy text search

Operations:
  rebuild  — full rebuild from all layer records
  search   — query the index by tags, keywords, or both
  stats    — show index health metrics
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from memory_classify import LAYERS

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
MEMORY_DIR = AMBIENT_ROOT / "memory"
INDEX_PATH = MEMORY_DIR / "index.json"
TRIGRAM_INDEX_PATH = MEMORY_DIR / "trigram_index.json"

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "or", "that",
    "the", "to", "was", "were", "will", "with",
    "的", "是", "了", "在", "有", "和", "就", "不", "人", "都",
}

LAYER_BOOST = {
    "semantic": 1.5,
    "procedural": 1.3,
    "governance": 1.2,
    "episodic": 1.0,
    "scratchpad": 0.3,
    "archive": 0.2,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def tokenize(text: str) -> list[str]:
    """Tokenize text into searchable terms."""
    tokens = re.findall(r"[a-z0-9\u4e00-\u9fff]+", text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def extract_trigrams(text: str) -> set[str]:
    """Extract character trigrams for fuzzy matching."""
    text = text.lower().strip()
    if len(text) < 3:
        return {text} if text else set()
    return {text[i : i + 3] for i in range(len(text) - 2)}


def recency_score(timestamp: str) -> float:
    """Score based on how recent the record is (0.0 to 1.0)."""
    if not timestamp:
        return 0.0
    try:
        ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        age_hours = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
        return math.exp(-age_hours / (24 * 7))
    except (ValueError, TypeError):
        return 0.0


class MemoryIndex:
    """In-memory inverted index over all memory layers."""

    def __init__(self):
        self.tag_index: dict[str, list[dict]] = defaultdict(list)
        self.token_index: dict[str, list[dict]] = defaultdict(list)
        self.records: list[dict[str, Any]] = []
        self.hashes: dict[str, str] = {}
        self.stats: dict[str, int] = Counter()

    def add_record(self, record: dict[str, Any], layer: str, line_num: int) -> None:
        """Add a record to the index."""
        content = record.get("content", "")
        tags = record.get("tags", [])
        timestamp = record.get("timestamp", "")
        source = record.get("source", "")

        entry = {
            "layer": layer,
            "line": line_num,
            "ts": timestamp,
            "src": source,
            "content_preview": content[:200] if isinstance(content, str) else str(content)[:200],
        }

        for tag in tags:
            self.tag_index[tag.lower()].append(entry)

        content_str = content if isinstance(content, str) else str(content)
        tokens = tokenize(content_str)
        for token in set(tokens):
            self.token_index[token].append(entry)

        self.records.append({"record": record, "layer": layer, "line": line_num})
        self.stats[layer] += 1

    def build_from_layers(self) -> dict[str, int]:
        """Rebuild the entire index from layer files."""
        self.tag_index.clear()
        self.token_index.clear()
        self.records.clear()
        self.hashes.clear()
        self.stats.clear()

        for layer in LAYERS:
            layer_file = MEMORY_DIR / layer / "records.jsonl"
            if not layer_file.exists():
                continue

            with layer_file.open("r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    self.add_record(record, layer, line_num)

        return dict(self.stats)

    def search(
        self,
        query: str,
        limit: int = 20,
        layer_filter: list[str] | None = None,
        tags_filter: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search the index with relevance scoring."""
        query_tokens = set(tokenize(query))
        query_tags = {t.lower() for t in (tags_filter or [])}
        candidates: dict[int, float] = {}

        for token in query_tokens:
            for entry in self.token_index.get(token, []):
                if layer_filter and entry["layer"] not in layer_filter:
                    continue
                idx = id(entry)
                candidates[idx] = candidates.get(idx, 0) + 1.0

        for tag in query_tags:
            for entry in self.tag_index.get(tag, []):
                if layer_filter and entry["layer"] not in layer_filter:
                    continue
                idx = id(entry)
                candidates[idx] = candidates.get(idx, 0) + 2.0

        if not query_tags:
            for token in query_tokens:
                for entry in self.tag_index.get(token, []):
                    if layer_filter and entry["layer"] not in layer_filter:
                        continue
                    idx = id(entry)
                    candidates[idx] = candidates.get(idx, 0) + 1.5

        scored: list[tuple[float, dict]] = []
        all_entries = {}

        for token in query_tokens:
            for entry in self.token_index.get(token, []):
                all_entries[id(entry)] = entry
        for tag in (query_tags or query_tokens):
            for entry in self.tag_index.get(tag, []):
                all_entries[id(entry)] = entry

        for entry_id, base_score in candidates.items():
            entry = all_entries.get(entry_id)
            if not entry:
                continue

            layer = entry["layer"]
            layer_mult = LAYER_BOOST.get(layer, 1.0)
            recency = recency_score(entry.get("ts", ""))
            token_coverage = base_score / max(len(query_tokens), 1)

            final_score = (base_score * layer_mult) + (recency * 0.5) + (token_coverage * 0.3)

            scored.append((final_score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, entry in scored[:limit]:
            results.append({
                "layer": entry["layer"],
                "source": entry.get("src", ""),
                "timestamp": entry.get("ts", ""),
                "content_preview": entry.get("content_preview", ""),
                "score": round(score, 3),
                "line": entry.get("line", 0),
            })

        return results

    def save(self) -> None:
        """Persist the index to disk."""
        index_data = {
            "built_at": utc_now(),
            "stats": dict(self.stats),
            "total_records": sum(self.stats.values()),
            "total_tags": len(self.tag_index),
            "total_tokens": len(self.token_index),
            "tags": {
                tag: [{"layer": e["layer"], "ts": e["ts"]} for e in entries[-5:]]
                for tag, entries in sorted(self.tag_index.items())
                if len(entries) <= 50
            },
            "hashes": self.hashes,
        }
        INDEX_PATH.write_text(
            json.dumps(index_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load_or_build(cls) -> "MemoryIndex":
        """Load existing index or build from scratch."""
        idx = cls()
        idx.build_from_layers()
        idx.save()
        return idx


def rebuild_index() -> dict[str, Any]:
    """Rebuild the full memory index."""
    idx = MemoryIndex()
    stats = idx.build_from_layers()
    idx.save()
    return {
        "status": "rebuilt",
        "built_at": utc_now(),
        "stats": stats,
        "total_records": sum(stats.values()),
        "total_tags": len(idx.tag_index),
        "total_tokens": len(idx.token_index),
    }


def search_index(
    query: str,
    limit: int = 20,
    layer_filter: list[str] | None = None,
    tags_filter: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Search the memory index."""
    idx = MemoryIndex()
    idx.build_from_layers()
    return idx.search(query, limit=limit, layer_filter=layer_filter, tags_filter=tags_filter)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Memory Inverted Index")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("rebuild")

    search_p = sub.add_parser("search")
    search_p.add_argument("query")
    search_p.add_argument("--limit", type=int, default=20)
    search_p.add_argument("--layer", action="append", default=[])
    search_p.add_argument("--tag", action="append", default=[])

    sub.add_parser("stats")

    args = parser.parse_args()

    if args.cmd == "rebuild":
        result = rebuild_index()
        print(json.dumps(result, indent=2))
    elif args.cmd == "search":
        results = search_index(
            args.query,
            limit=args.limit,
            layer_filter=args.layer or None,
            tags_filter=args.tag or None,
        )
        for r in results:
            print(json.dumps(r, ensure_ascii=False))
    else:
        if INDEX_PATH.exists():
            data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
            print(json.dumps({k: v for k, v in data.items() if k != "tags"}, indent=2))
        else:
            print("No index found. Run: python memory_index.py rebuild")
