#!/usr/bin/env python3
"""Query the Ambient OS self-model from state/system_state.json."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, stable_json


ROOT = Path(__file__).resolve().parents[1]
STATE_JSON = ROOT / "state" / "system_state.json"
DASHBOARD_HTML = ROOT / "dashboard" / "index.html"
DAILY_DIGEST = ROOT / "dashboard" / "daily_digest.md"

QUERIES = ("health", "incidents", "memory", "reflex", "dashboard", "digest", "summary")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state() -> dict[str, Any]:
    if not STATE_JSON.exists():
        raise FileNotFoundError("state/system_state.json is missing; run system-state-build first")
    return json.loads(STATE_JSON.read_text(encoding="utf-8"))


def source_for(state: dict[str, Any], key: str) -> str:
    source = state.get("authoritative_sources", {}).get(key, {})
    path = source.get("path", "unknown")
    field = source.get("field") or source.get("method") or ""
    return f"{path} ({field})" if field else path


def query_payload(state: dict[str, Any], query: str) -> dict[str, Any]:
    common = {
        "query": query,
        "queried_at": utc_now(),
        "state_file": str(STATE_JSON.relative_to(ROOT)),
        "state_generated_at": state.get("generated_at"),
        "recommendations_only": True,
        "corrective_actions": "none",
    }

    if query == "health":
        return {
            **common,
            "health_score": state.get("health_score"),
            "health_risk": state.get("health_risk"),
            "trend": state.get("trend"),
            "subsystems": state.get("subsystems", {}),
            "baseline_deviation": state.get("baseline_deviation", {}),
            "source": source_for(state, "health_score"),
        }

    if query == "incidents":
        return {
            **common,
            "incident_count": state.get("incident_count"),
            "repeated_anomaly_count": state.get("repeated_anomaly_count"),
            "repeated_anomalies": state.get("repeated_anomalies", {}),
            "source": source_for(state, "incident_count"),
            "repeated_anomalies_source": source_for(state, "repeated_anomalies"),
        }

    if query == "memory":
        return {
            **common,
            "dmn_append_count": state.get("dmn_append_count"),
            "memory_status": state.get("memory_status", {}),
            "latest_telemetry_snapshot": state.get("latest_telemetry_snapshot"),
            "docker_context": state.get("docker_context", {}),
            "source": source_for(state, "dmn_append_count"),
        }

    if query == "reflex":
        return {
            **common,
            "reflex_confidence": state.get("latest_reflex_confidence"),
            "risk_class": state.get("current_risk_class"),
            "display_risk": state.get("display_risk"),
            "recommendations": state.get("recommendations", []),
            "source": source_for(state, "reflex_confidence"),
        }

    if query == "dashboard":
        return {
            **common,
            "dashboard": str(DASHBOARD_HTML.relative_to(ROOT)),
            "exists": DASHBOARD_HTML.exists(),
            "values": {
                "health_score": state.get("health_score"),
                "incident_count": state.get("incident_count"),
                "dmn_append_count": state.get("dmn_append_count"),
                "reflex_confidence": state.get("latest_reflex_confidence"),
                "baseline_deviation": (state.get("baseline_deviation") or {}).get("overall_severity"),
            },
            "source": str(STATE_JSON.relative_to(ROOT)),
        }

    if query == "digest":
        return {
            **common,
            "daily_digest": str(DAILY_DIGEST.relative_to(ROOT)),
            "exists": DAILY_DIGEST.exists(),
            "values": {
                "health_score": state.get("health_score"),
                "incident_count": state.get("incident_count"),
                "dmn_append_count": state.get("dmn_append_count"),
                "reflex_confidence": state.get("latest_reflex_confidence"),
                "baseline_deviation": (state.get("baseline_deviation") or {}).get("overall_severity"),
            },
            "source": str(STATE_JSON.relative_to(ROOT)),
        }

    return {
        **common,
        "health_score": state.get("health_score"),
        "health_risk": state.get("health_risk"),
        "trend": state.get("trend"),
        "incident_count": state.get("incident_count"),
        "repeated_anomaly_count": state.get("repeated_anomaly_count"),
        "dmn_append_count": state.get("dmn_append_count"),
        "reflex_confidence": state.get("latest_reflex_confidence"),
        "risk_class": state.get("current_risk_class"),
        "baseline_deviation": (state.get("baseline_deviation") or {}).get("overall_severity"),
        "stale_state_detection": (state.get("validation") or {}).get("stale_state_detection", {}),
        "recommendations": state.get("recommendations", []),
        "sources": state.get("authoritative_sources", {}),
    }


def format_lines(payload: dict[str, Any]) -> list[str]:
    query = payload["query"]
    lines = [
        f"Self-model query: {query}",
        f"State: {payload['state_file']} generated {payload.get('state_generated_at')}",
        "Corrective actions: none. Recommendations only.",
    ]

    if query == "health":
        lines.extend(
            [
                f"Health score: {payload['health_score']} ({payload['health_risk']})",
                f"Trend: {payload['trend']}",
                f"Baseline deviation: {payload['baseline_deviation'].get('overall_severity')}",
                "Subsystems:",
            ]
        )
        for name, data in payload["subsystems"].items():
            lines.append(f"- {name}: score={data.get('score')} penalty={data.get('incident_penalty')}")
        lines.append(f"Source: {payload['source']}")
        return lines

    if query == "incidents":
        repeated = payload["repeated_anomalies"] or {}
        repeated_text = ", ".join(f"{key}: {value}" for key, value in repeated.items()) or "none"
        lines.extend(
            [
                f"Incident count: {payload['incident_count']}",
                f"Repeated anomaly count: {payload['repeated_anomaly_count']}",
                f"Repeated anomalies: {repeated_text}",
                f"Source: {payload['source']}",
                f"Repeated source: {payload['repeated_anomalies_source']}",
            ]
        )
        return lines

    if query == "memory":
        status = payload["memory_status"]
        vm = payload["docker_context"].get("vm", {})
        lines.extend(
            [
                f"DMN append count: {payload['dmn_append_count']}",
                f"Memory used: {status.get('used_percent')}%",
                f"Memory risk: {status.get('true_risk')}",
                f"Scoring artifact: {status.get('scoring_artifact')}",
                f"Free bytes: {status.get('free_bytes')}",
                f"Docker VM: detected={vm.get('detected')} memory_mib={vm.get('memory_mib')} rss_mb={vm.get('rss_mb')}",
                f"Latest telemetry: {payload['latest_telemetry_snapshot']}",
                f"Source: {payload['source']}",
            ]
        )
        return lines

    if query == "reflex":
        lines.extend(
            [
                f"Reflex confidence: {payload['reflex_confidence']}",
                f"Risk class: {payload['risk_class']}",
                f"Display risk: {payload['display_risk']}",
                "Recommendations:",
            ]
        )
        for recommendation in payload["recommendations"]:
            lines.append(f"- {recommendation}")
        lines.append(f"Source: {payload['source']}")
        return lines

    if query in {"dashboard", "digest"}:
        label = "Dashboard" if query == "dashboard" else "Daily digest"
        path_key = "dashboard" if query == "dashboard" else "daily_digest"
        lines.extend(
            [
                f"{label}: {payload[path_key]}",
                f"Exists: {payload['exists']}",
                f"Health score: {payload['values']['health_score']}",
                f"Incident count: {payload['values']['incident_count']}",
                f"DMN append count: {payload['values']['dmn_append_count']}",
                f"Reflex confidence: {payload['values']['reflex_confidence']}",
                f"Baseline deviation: {payload['values']['baseline_deviation']}",
                f"Source: {payload['source']}",
            ]
        )
        return lines

    lines.extend(
        [
            f"Health score: {payload['health_score']} ({payload['health_risk']})",
            f"Trend: {payload['trend']}",
            f"Incident count: {payload['incident_count']}",
            f"Repeated anomaly count: {payload['repeated_anomaly_count']}",
            f"DMN append count: {payload['dmn_append_count']}",
            f"Reflex confidence: {payload['reflex_confidence']} ({payload['risk_class']})",
            f"Baseline deviation: {payload['baseline_deviation']}",
            f"Stale state detection: {payload['stale_state_detection'].get('status')}",
            "Recommendations:",
        ]
    )
    for recommendation in payload["recommendations"]:
        lines.append(f"- {recommendation}")
    return lines


def run_query(query: str, json_output: bool) -> dict[str, Any]:
    state = load_state()
    payload = query_payload(state, query)
    log_action(
        f"state:query:{query}",
        "completed",
        "ALLOW",
        {
            "query": query,
            "output": "json" if json_output else "text",
            "state": str(STATE_JSON.relative_to(ROOT)),
            "recommendations_only": True,
        },
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Query Ambient OS system_state.json.")
    parser.add_argument("query", choices=QUERIES)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()
    payload = run_query(args.query, args.json)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("\n".join(format_lines(payload)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
