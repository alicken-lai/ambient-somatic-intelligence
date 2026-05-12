#!/usr/bin/env python3
"""Unified read-only recall over Ambient OS memory sources."""

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DMN_FILE = ROOT / "memory" / "dmn.jsonl"
LOGS_DIR = ROOT / "logs"
PALACE_JSON = ROOT / "tools" / "mempalace" / "palace.json"
STATE_JSON = ROOT / "state" / "system_state.json"

SOURCE_PATHS = {
    "dmn": DMN_FILE,
    "night_logs": LOGS_DIR,
    "mempalace": PALACE_JSON,
    "system_state": STATE_JSON,
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "for",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def tokenize(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.casefold())
        if token and token not in STOP_WORDS
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
    return min(0.05, 0.05 * math.exp(-age_days / 30.0))


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def compact_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def load_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def confidence_for(query: str, content: str, tags: list[str], timestamp: str) -> tuple[float, dict[str, Any]]:
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

    if exact:
        confidence = clamp(0.95 + recency_boost(timestamp), 0.90, 1.00)
        band = "exact"
    elif tag_match:
        confidence = clamp(0.78 + (0.05 * len(tag_overlap)) + recency_boost(timestamp), 0.70, 0.89)
        band = "tag"
    elif semantic_match:
        confidence = clamp(0.40 + (0.25 * overlap_ratio) + recency_boost(timestamp), 0.40, 0.69)
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
    }


def make_match(
    *,
    query: str,
    source: str,
    source_type: str,
    content: str,
    tags: list[str] | None = None,
    timestamp: str = "",
) -> dict[str, Any] | None:
    clean_tags = [str(tag) for tag in (tags or []) if str(tag)]
    confidence, rank = confidence_for(query, content, clean_tags, timestamp)
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


def search_dmn(query: str) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    if not DMN_FILE.exists():
        return matches
    with DMN_FILE.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            content = str(record.get("content", ""))
            tags = record.get("tags") if isinstance(record.get("tags"), list) else []
            timestamp = str(record.get("timestamp", ""))
            payload = compact_json(record)
            match = make_match(
                query=query,
                source=f"{DMN_FILE.relative_to(ROOT)}:{line_number}",
                source_type="dmn",
                content=content or payload,
                tags=[str(tag) for tag in tags],
                timestamp=timestamp,
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
                        source=f"{path.relative_to(ROOT)}:{line_number}",
                        source_type="night_log",
                        content=text[:1000],
                        tags=[],
                        timestamp="",
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
                source=f"{PALACE_JSON.relative_to(ROOT)}:{node.get('event_id', domain)}",
                source_type="mempalace",
                content=content,
                tags=tags,
                timestamp=str(node.get("timestamp", palace.get("generated_at", ""))),
            )
            if match:
                matches.append(match)
    return matches


def flatten_state(prefix: str, value: Any) -> list[tuple[str, Any]]:
    if isinstance(value, dict):
        rows: list[tuple[str, Any]] = []
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(flatten_state(child_prefix, child))
        return rows
    if isinstance(value, list):
        return [(prefix, value)]
    return [(prefix, value)]


def search_system_state(query: str) -> list[dict[str, Any]]:
    state = load_json(STATE_JSON)
    if not isinstance(state, dict):
        return []
    matches: list[dict[str, Any]] = []
    generated_at = str(state.get("generated_at", ""))
    for key, value in flatten_state("", state):
        content = f"{key}: {compact_json(value)}"
        match = make_match(
            query=query,
            source=f"{STATE_JSON.relative_to(ROOT)}:{key}",
            source_type="system_state",
            content=content[:1000],
            tags=[part for part in key.split(".") if part],
            timestamp=generated_at,
        )
        if match:
            matches.append(match)
    return matches


def dedupe(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for match in matches:
        key = (match["source_type"], match["source"], match["content"])
        existing = deduped.get(key)
        if not existing or match["confidence"] > existing["confidence"]:
            deduped[key] = match
    return list(deduped.values())


def rank_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(match: dict[str, Any]) -> tuple[float, float, float, float, float]:
        rank = match.get("_rank", {})
        return (
            1.0 if rank.get("exact") else 0.0,
            float(rank.get("semantic_overlap") or 0.0),
            1.0 if rank.get("tag_match") else 0.0,
            float(rank.get("recency") or 0.0),
            float(match.get("confidence") or 0.0),
        )

    ranked = sorted(matches, key=sort_key, reverse=True)
    for match in ranked:
        match.pop("_rank", None)
    return ranked


def memory_recall(query: str) -> dict[str, Any]:
    query = str(query or "").strip()
    timestamp = utc_now()
    sources = [str(path.relative_to(ROOT)) if path.is_absolute() else str(path) for path in SOURCE_PATHS.values()]
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
    matches.extend(search_dmn(query))
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
    parser = argparse.ArgumentParser(description="Unified Ambient OS memory recall.")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    payload = memory_recall(args.query)
    payload["matches"] = payload["matches"][: max(1, args.limit)]
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
