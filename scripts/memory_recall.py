"""
Unified Memory Recall — Phase 1 Upgrade.

Layered-aware memory recall with priority-based search:
  1. semantic   (highest priority — stable knowledge)
  2. procedural (workflows, solutions)
  3. governance (policy decisions, incidents)
  4. episodic   (task history, debug sessions)
  5. scratchpad (lowest priority — transient data)

Uses the inverted index for fast lookup, with fallback to linear scan.
Maintains backward compatibility with the original recall_schema.json contract.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from memory_classify import LAYERS

ROOT = Path(__file__).resolve().parents[1]
AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", ROOT))
MEMORY_DIR = AMBIENT_ROOT / "memory"
DMN_FILE = MEMORY_DIR / "dmn.jsonl"
LOGS_DIR = AMBIENT_ROOT / "logs"
PALACE_JSON = AMBIENT_ROOT / "tools" / "mempalace" / "palace.json"
STATE_JSON = AMBIENT_ROOT / "state" / "system_state.json"

LAYER_SEARCH_ORDER = ["semantic", "procedural", "governance", "episodic", "scratchpad"]

LAYER_WEIGHT = {
    "semantic": 1.5,
    "procedural": 1.3,
    "governance": 1.2,
    "episodic": 1.0,
    "scratchpad": 0.3,
    "archive": 0.1,
}

SOURCE_PATHS = {
    "layered_memory": MEMORY_DIR,
    "night_logs": LOGS_DIR,
    "mempalace": PALACE_JSON,
    "system_state": STATE_JSON,
}

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "or", "that",
    "the", "to", "was", "were", "will", "with",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def tokenize(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9\u4e00-\u9fff]+", value.casefold())
        if token and token not in STOP_WORDS and len(token) > 1
    }


def parse_timestamp(value: str) -> float:
    if not value:
        return 0.0
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        return 0.0


def recency_boost(timestamp: str) -> float:
    epoch = parse_timestamp(timestamp)
    if not epoch:
        return 0.0
    age_days = max(0.0, (datetime.now(timezone.utc).timestamp() - epoch) / 86400.0)
    return min(0.05, 0.05 * math.exp(-age_days / 7.0))


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def compact_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def load_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def confidence_for(
    query: str,
    content: str,
    tags: list[str],
    timestamp: str,
    layer: str = "episodic",
) -> tuple[float, dict[str, Any]]:
    """Calculate confidence score with layer-aware boosting."""
    query_folded = query.casefold().strip()
    content_folded = content.casefold()
    tag_text = " ".join(tags).casefold()
    query_tokens = tokenize(query)
    content_tokens = tokenize(content)
    tag_tokens = tokenize(tag_text)
    overlap_tokens = query_tokens & content_tokens
    tag_overlap = query_tokens & tag_tokens
    overlap_ratio = (len(overlap_tokens) / len(query_tokens)) if query_tokens else 0.0

    exact = bool(query_folded and query_folded in content_folded)
    if len(query_tokens) <= 2:
        tag_match = bool(query_tokens) and query_tokens <= tag_tokens
    else:
        tag_match = len(tag_overlap) >= 2
    semantic_match = False
    if len(query_tokens) <= 2:
        semantic_match = bool(query_tokens) and query_tokens <= content_tokens
    else:
        semantic_match = overlap_ratio >= 0.5 and len(overlap_tokens) >= 2

    layer_mult = LAYER_WEIGHT.get(layer, 1.0)

    if exact:
        base = 0.95 + recency_boost(timestamp)
        confidence = clamp(base * layer_mult, 0.70, 1.00)
        band = "exact"
    elif tag_match:
        base = 0.78 + (0.05 * len(tag_overlap)) + recency_boost(timestamp)
        confidence = clamp(base * layer_mult, 0.50, 0.94)
        band = "tag"
    elif semantic_match:
        base = 0.40 + (0.25 * overlap_ratio) + recency_boost(timestamp)
        confidence = clamp(base * layer_mult, 0.20, 0.79)
        band = "semantic"
    else:
        confidence = 0.0
        band = "none"

    return round(confidence, 4), {
        "band": band,
        "exact": exact,
        "tag_match": tag_match,
        "semantic_overlap": round(overlap_ratio, 4),
        "recency": parse_timestamp(timestamp),
        "layer": layer,
        "layer_weight": layer_mult,
    }


def make_match(
    *,
    query: str,
    source: str,
    source_type: str,
    content: str,
    tags: list[str] | None = None,
    timestamp: str = "",
    layer: str = "episodic",
) -> dict[str, Any] | None:
    clean_tags = [str(tag) for tag in (tags or []) if str(tag)]
    confidence, rank = confidence_for(query, content, clean_tags, timestamp, layer)
    if confidence <= 0.0:
        return None
    return {
        "source": source,
        "source_type": source_type,
        "content": content,
        "tags": clean_tags,
        "timestamp": timestamp,
        "confidence": confidence,
        "_rank": rank,
    }


def search_layered_memory(query: str) -> list[dict[str, Any]]:
    """Search all memory layers in priority order."""
    matches: list[dict[str, Any]] = []

    for layer in LAYER_SEARCH_ORDER:
        layer_file = MEMORY_DIR / layer / "records.jsonl"
        if not layer_file.exists():
            continue

        with layer_file.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                content = str(record.get("content", ""))
                tags = record.get("tags") if isinstance(record.get("tags"), list) else []
                timestamp = str(record.get("timestamp", ""))

                match = make_match(
                    query=query,
                    source=f"memory/{layer}/records.jsonl:{line_number}",
                    source_type=f"layered_{layer}",
                    content=content[:2000],
                    tags=[str(tag) for tag in tags],
                    timestamp=timestamp,
                    layer=layer,
                )
                if match:
                    matches.append(match)

    return matches


def search_night_logs(query: str) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    if not LOGS_DIR.exists():
        return matches
    for pattern in ("*.log", "*.md", "*.jsonl"):
        for path in sorted(LOGS_DIR.glob(pattern)):
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for line_number, line in enumerate(handle, start=1):
                    text = line.strip()
                    if not text:
                        continue
                    match = make_match(
                        query=query,
                        source=f"{path.relative_to(AMBIENT_ROOT)}:{line_number}",
                        source_type="night_log",
                        content=text[:1000],
                        tags=[],
                        timestamp="",
                        layer="episodic",
                    )
                    if match:
                        matches.append(match)
    return matches


def search_mempalace(query: str) -> list[dict[str, Any]]:
    palace = load_json(PALACE_JSON)
    if not isinstance(palace, dict):
        return []
    matches: list[dict[str, Any]] = []
    for domain, nodes in (palace.get("palace_nodes") or {}).items():
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            tags = [
                str(domain),
                str(node.get("anomaly_type", "")),
                str(node.get("event_id", "")),
            ]
            content = compact_json(node)
            match = make_match(
                query=query,
                source=f"tools/mempalace/palace.json:{node.get('event_id', domain)}",
                source_type="mempalace",
                content=content,
                tags=tags,
                timestamp=str(node.get("timestamp", palace.get("generated_at", ""))),
                layer="semantic",
            )
            if match:
                matches.append(match)
    return matches


def search_system_state(query: str) -> list[dict[str, Any]]:
    state = load_json(STATE_JSON)
    if not isinstance(state, dict):
        return []
    matches: list[dict[str, Any]] = []
    generated_at = str(state.get("generated_at", ""))

    def flatten(prefix: str, value: Any) -> list[tuple[str, Any]]:
        if isinstance(value, dict):
            rows: list[tuple[str, Any]] = []
            for key, child in value.items():
                child_prefix = f"{prefix}.{key}" if prefix else str(key)
                rows.extend(flatten(child_prefix, child))
            return rows
        return [(prefix, value)]

    for key, value in flatten("", state):
        content = f"{key}: {compact_json(value)}"
        match = make_match(
            query=query,
            source=f"state/system_state.json:{key}",
            source_type="system_state",
            content=content[:1000],
            tags=[part for part in key.split(".") if part],
            timestamp=generated_at,
            layer="episodic",
        )
        if match:
            matches.append(match)
    return matches


def dedupe(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for match in matches:
        key = f"{match['source_type']}:{match['source']}:{match['content'][:100]}"
        existing = deduped.get(key)
        if not existing or match["confidence"] > existing["confidence"]:
            deduped[key] = match
    return list(deduped.values())


def rank_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(match: dict[str, Any]) -> tuple[float, float, float, float, float]:
        rank = match.get("_rank", {})
        layer_weight = rank.get("layer_weight", 1.0)
        return (
            layer_weight,
            1.0 if rank.get("exact") else 0.0,
            float(rank.get("semantic_overlap") or 0.0),
            1.0 if rank.get("tag_match") else 0.0,
            float(match.get("confidence") or 0.0),
        )

    ranked = sorted(matches, key=sort_key, reverse=True)
    for match in ranked:
        match.pop("_rank", None)
    return ranked


def memory_recall(query: str) -> dict[str, Any]:
    """Unified memory recall with layer-priority search."""
    query = str(query or "").strip()
    timestamp = utc_now()
    sources = list(SOURCE_PATHS.keys())

    if not query:
        return {
            "query": query,
            "sources": sources,
            "matches": [],
            "confidence": 0.0,
            "null_recall": True,
            "timestamp": timestamp,
        }

    matches: list[dict[str, Any]] = []
    matches.extend(search_layered_memory(query))
    matches.extend(search_night_logs(query))
    matches.extend(search_mempalace(query))
    matches.extend(search_system_state(query))

    ranked = rank_matches(dedupe(matches))
    confidence = max((match["confidence"] for match in ranked), default=0.0)

    return {
        "query": query,
        "sources": sources,
        "matches": ranked,
        "confidence": confidence,
        "null_recall": not ranked,
        "timestamp": timestamp,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified Ambient OS memory recall (Phase 1).")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    payload = memory_recall(args.query)
    payload["matches"] = payload["matches"][: max(1, args.limit)]
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
