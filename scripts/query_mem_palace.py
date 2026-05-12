#!/usr/bin/env python3
"""Query the MemPalace spatial episodic memory."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, stable_json


ROOT = Path(__file__).resolve().parents[1]
PALACE_JSON = ROOT / "tools" / "mempalace" / "palace.json"
VALID_QUERIES = ("summary", "domain", "anomaly_type", "confidence", "linked_events", "lessons")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_palace() -> dict[str, Any]:
    if not PALACE_JSON.exists():
        raise FileNotFoundError("tools/mempalace/palace.json is missing; run mem-palace-build first")
    return json.loads(PALACE_JSON.read_text(encoding="utf-8"))


def flatten_nodes(palace: dict[str, Any]) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for domain, items in (palace.get("palace_nodes") or {}).items():
        for item in items or []:
            nodes.append({**item, "domain": domain})
    return nodes


def filter_nodes(nodes: list[dict[str, Any]], query: str, domain: str | None, anomaly_type: str | None) -> list[dict[str, Any]]:
    filtered = nodes
    if domain:
        filtered = [node for node in filtered if node.get("domain") == domain]
    if anomaly_type:
        filtered = [node for node in filtered if str(node.get("anomaly_type")) == anomaly_type]
    if query == "confidence":
        filtered = sorted(filtered, key=lambda node: float(node.get("confidence") or 0.0), reverse=True)
    return filtered


def query_payload(query: str, domain: str | None = None, anomaly_type: str | None = None) -> dict[str, Any]:
    palace = load_palace()
    nodes = flatten_nodes(palace)
    filtered = filter_nodes(nodes, query, domain, anomaly_type)
    common = {
        "query": query,
        "queried_at": utc_now(),
        "palace_file": str(PALACE_JSON.relative_to(ROOT)),
        "palace_generated_at": palace.get("generated_at"),
        "recommendations_only": True,
        "corrective_actions": "none",
        "domain": domain,
        "anomaly_type": anomaly_type,
    }

    if query == "summary":
        return {
            **common,
            "node_count": palace.get("node_count", len(nodes)),
            "link_count": palace.get("link_count", len(palace.get("palace_links", []))),
            "domains": palace.get("domains", []),
            "domain_counts": {name: len(palace.get("palace_nodes", {}).get(name, [])) for name in palace.get("domains", [])},
        }

    if query == "domain":
        if not domain:
            domain = "system_health"
            filtered = filter_nodes(nodes, query, domain, anomaly_type)
        return {
            **common,
            "nodes": filtered,
            "node_count": len(filtered),
        }

    if query == "anomaly_type":
        return {
            **common,
            "nodes": filtered,
            "node_count": len(filtered),
        }

    if query == "confidence":
        return {
            **common,
            "nodes": filtered,
            "node_count": len(filtered),
            "highest_confidence": filtered[0].get("confidence") if filtered else None,
            "lowest_confidence": filtered[-1].get("confidence") if filtered else None,
        }

    if query == "linked_events":
        nodes_with_links = [node for node in filtered if node.get("linked_events")]
        return {
            **common,
            "nodes": nodes_with_links,
            "node_count": len(nodes_with_links),
        }

    if query == "lessons":
        nodes_with_lessons = [node for node in filtered if node.get("lessons")]
        lessons = [lesson for node in nodes_with_lessons for lesson in node.get("lessons", [])]
        return {
            **common,
            "nodes": nodes_with_lessons,
            "node_count": len(nodes_with_lessons),
            "lessons": lessons,
        }

    return {
        **common,
        "nodes": filtered,
        "node_count": len(filtered),
    }


def format_lines(payload: dict[str, Any]) -> list[str]:
    query = payload["query"]
    lines = [
        f"MemPalace query: {query}",
        f"Palace: {payload['palace_file']} generated {payload.get('palace_generated_at')}",
        "Corrective actions: none. Recommendations only.",
    ]

    if query == "summary":
        lines.extend(
            [
                f"Node count: {payload['node_count']}",
                f"Link count: {payload['link_count']}",
                f"Domains: {', '.join(payload['domains'])}",
            ]
        )
        for domain, count in payload["domain_counts"].items():
            lines.append(f"- {domain}: {count}")
        return lines

    if query == "confidence":
        lines.extend([f"Node count: {payload['node_count']}"])
        if payload["node_count"]:
            lines.append(f"Highest confidence: {payload['highest_confidence']}")
            lines.append(f"Lowest confidence: {payload['lowest_confidence']}")
        for node in payload["nodes"]:
            lines.append(f"- {node['domain']} {node['event_id']}: confidence={node.get('confidence')}")
        return lines

    if query == "linked_events":
        lines.append(f"Node count: {payload['node_count']}")
        for node in payload["nodes"]:
            lines.append(f"- {node['domain']} {node['event_id']}")
            for event in node.get("linked_events", []):
                lines.append(f"  - {event}")
        return lines

    if query == "lessons":
        lines.append(f"Node count: {payload['node_count']}")
        for lesson in payload.get("lessons", []):
            lines.append(f"- {lesson}")
        return lines

    lines.append(f"Node count: {payload['node_count']}")
    if payload.get("domain"):
        lines.append(f"Domain: {payload['domain']}")
    if payload.get("anomaly_type"):
        lines.append(f"Anomaly type: {payload['anomaly_type']}")
    for node in payload["nodes"]:
        lines.extend(
            [
                f"- {node['domain']} {node['event_id']}",
                f"  anomaly_type: {node.get('anomaly_type')}",
                f"  confidence: {node.get('confidence')}",
                f"  explanation: {node.get('explanation')}",
            ]
        )
    return lines


def run_query(query: str, domain: str | None, anomaly_type: str | None, json_output: bool) -> dict[str, Any]:
    payload = query_payload(query, domain=domain, anomaly_type=anomaly_type)
    log_action(
        f"mem-palace:query:{query}",
        "completed",
        "ALLOW",
        {
            "query": query,
            "output": "json" if json_output else "text",
            "domain": domain,
            "anomaly_type": anomaly_type,
            "palace": str(PALACE_JSON.relative_to(ROOT)),
            "recommendations_only": True,
        },
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Query the MemPalace spatial episodic memory.")
    parser.add_argument("query", choices=VALID_QUERIES)
    parser.add_argument("--domain", choices=[
        "system_health",
        "memory_pressure",
        "docker_runtime",
        "guardian_reflex",
        "visual_layer",
        "operator_decisions",
    ])
    parser.add_argument("--anomaly-type")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = run_query(args.query, args.domain, args.anomaly_type, args.json)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("\n".join(format_lines(payload)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
