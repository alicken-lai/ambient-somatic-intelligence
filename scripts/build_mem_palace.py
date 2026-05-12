#!/usr/bin/env python3
"""Build a spatial episodic memory palace from Guardian artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, record_checksum, stable_json
from build_system_state import build_system_state
from remember import append_memory


ROOT = Path(__file__).resolve().parents[1]
STATE_JSON = ROOT / "state" / "system_state.json"
INCIDENT_INDEX = ROOT / "guardian" / "incidents" / "index.json"
SIMULATION_JSON = ROOT / "guardian" / "simulations" / "latest_simulation.json"
DREAM_JSON = ROOT / "guardian" / "dreams" / "latest_dream.json"
QUEUE_JSON = ROOT / "guardian" / "recalibration" / "queue.json"
REFLECTION_MD = ROOT / "docs" / "reflections" / "latest.md"
PALACE_DIR = ROOT / "tools" / "mempalace"
PALACE_JSON = PALACE_DIR / "palace.json"
PALACE_MD = PALACE_DIR / "palace.md"

DOMAINS = (
    "system_health",
    "memory_pressure",
    "docker_runtime",
    "guardian_reflex",
    "visual_layer",
    "operator_decisions",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def recent_incidents(index: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    incidents = sorted(index.get("incidents", []), key=lambda item: str(item.get("timestamp", "")))
    return incidents[-limit:]


def first_anomaly(incident: dict[str, Any]) -> dict[str, Any]:
    anomalies = incident.get("anomalies", [])
    return anomalies[0] if anomalies else {}


def node(
    *,
    domain: str,
    event_id: str,
    timestamp: str,
    anomaly_type: str,
    confidence: float | int | None,
    explanation: str,
    linked_events: list[str],
    lessons: list[str],
) -> dict[str, Any]:
    return {
        "domain": domain,
        "event_id": event_id,
        "timestamp": timestamp,
        "anomaly_type": anomaly_type,
        "confidence": confidence,
        "explanation": explanation,
        "linked_events": linked_events,
        "lessons": lessons,
    }


def build_palace() -> dict[str, Any]:
    state = load_json(STATE_JSON)
    if not state:
        raise RuntimeError("state/system_state.json is missing; run system-state-build first")
    incidents = load_json(INCIDENT_INDEX)
    simulation = load_json(SIMULATION_JSON)
    dream = load_json(DREAM_JSON)
    queue = load_json(QUEUE_JSON)
    reflection = REFLECTION_MD.read_text(encoding="utf-8") if REFLECTION_MD.exists() else ""
    recent = recent_incidents(incidents, 5)
    recent_events = [str(item.get("incident")) for item in recent]
    dream_events = [str(item.get("incident")) for item in dream.get("replays", []) if item.get("incident")]
    queue_events = [str(item.get("incident")) for item in queue.get("items", []) if item.get("incident")]
    runtime_links = list(dict.fromkeys(recent_events + dream_events + queue_events))

    palace_nodes: dict[str, list[dict[str, Any]]] = {domain: [] for domain in DOMAINS}

    for incident in recent:
        anomaly = first_anomaly(incident)
        rule = str(anomaly.get("rule", "unknown"))
        timestamp = str(incident.get("timestamp", "unknown"))
        event_id = str(incident.get("incident", f"incident:{timestamp}"))
        lesson = str(anomaly.get("recommendation") or "Keep watching repeated memory pressure.")
        if "memory" in rule:
            domain = "memory_pressure"
        elif "disk" in rule or "load" in rule or "cpu" in rule or "process" in rule:
            domain = "system_health"
        else:
            domain = "guardian_reflex"
        palace_nodes[domain].append(
            node(
                domain=domain,
                event_id=event_id,
                timestamp=timestamp,
                anomaly_type=rule,
                confidence=anomaly.get("confidence", state.get("latest_reflex_confidence")),
                explanation=str(anomaly.get("recommendation") or incident.get("incident")),
                linked_events=[str(anomaly.get("evidence") or incident.get("incident"))],
                lessons=[lesson],
            )
        )

    if simulation:
        predicted = simulation.get("predicted_risk", {})
        palace_nodes["system_health"].append(
            node(
                domain="system_health",
                event_id="simulation:" + str(simulation.get("generated_at", "latest")),
                timestamp=str(simulation.get("generated_at", "unknown")),
                anomaly_type=str(predicted.get("level", "review")),
                confidence=predicted.get("confidence", 0.0),
                explanation="Simulation predicts memory pressure remains the primary driver over 2h.",
                linked_events=[str(simulation.get("latest_telemetry", "unknown"))],
                lessons=["Use simulation horizons to prioritize review before drift compounds."],
            )
        )

    if dream:
        palace_nodes["operator_decisions"].append(
            node(
                domain="operator_decisions",
                event_id="dream:" + str(dream.get("generated_at", "latest")),
                timestamp=str(dream.get("generated_at", "unknown")),
                anomaly_type="recalibration_candidate",
                confidence=0.2,
                explanation="Dream replay surfaced recalibration candidates for repeated memory warnings.",
                linked_events=[str(item.get("incident")) for item in dream.get("recalibration_candidates", []) if item.get("incident")],
                lessons=["Queue repeated rule-family observations for review before changing calibration."],
            )
        )
        palace_nodes["visual_layer"].append(
            node(
                domain="visual_layer",
                event_id="dream-brief:" + str(dream.get("generated_at", "latest")),
                timestamp=str(dream.get("generated_at", "unknown")),
                anomaly_type="narrative_replay",
                confidence=0.1,
                explanation="The reflection and briefing surfaces preserve a readable replay of prior state.",
                linked_events=[str(REFLECTION_MD.relative_to(ROOT)) if REFLECTION_MD.exists() else "docs/reflections/latest.md"],
                lessons=["Keep human-readable summaries synchronized with the underlying state."],
            )
        )

    if reflection:
        palace_nodes["visual_layer"].append(
            node(
                domain="visual_layer",
                event_id="reflection:" + str(state.get("generated_at", "latest")),
                timestamp=str(state.get("generated_at", "unknown")),
                anomaly_type="self_reflection",
                confidence=state.get("latest_reflex_confidence"),
                explanation="Self-reflection carries the current watch posture and the memory-pressure narrative.",
                linked_events=[str(REFLECTION_MD.relative_to(ROOT))],
                lessons=["Keep self-reflection aligned with the latest operator briefing and anomaly explanation."],
            )
        )

    if queue:
        for item in queue.get("items", []):
            palace_nodes["guardian_reflex"].append(
                node(
                    domain="guardian_reflex",
                    event_id="queue:" + str(item.get("incident", "unknown")),
                    timestamp=str(queue.get("generated_at", "unknown")),
                    anomaly_type=str(item.get("candidate_rule", "unknown")),
                    confidence=item.get("recommended_confidence", 0.0),
                    explanation=str(item.get("candidate_suggestion", "Review candidate")),
                linked_events=list(dict.fromkeys(item.get("source_evidence", []))),
                lessons=["Treat recalibration as review-only until approval is granted."],
            )
        )

    palace_nodes["docker_runtime"].append(
        node(
            domain="docker_runtime",
            event_id="docker:" + str(state.get("generated_at", "latest")),
            timestamp=str(state.get("generated_at", "unknown")),
            anomaly_type="runtime_context",
                confidence=state.get("latest_reflex_confidence"),
                explanation="Docker runtime remained lightly loaded while the memory-scoring artifact persisted.",
                linked_events=runtime_links,
                lessons=["Keep docker runtime context attached to memory-pressure events."],
            )
        )

    palace_links: list[dict[str, Any]] = []
    for domain, nodes in palace_nodes.items():
        for index, item in enumerate(nodes):
            for other in nodes[index + 1 :]:
                palace_links.append(
                    {
                        "source": item["event_id"],
                        "target": other["event_id"],
                        "relation": "same_domain",
                        "domain": domain,
                    }
                )
    for incident in recent:
        incident_id = str(incident.get("incident"))
        first = first_anomaly(incident)
        for other_domain in ("memory_pressure", "guardian_reflex", "system_health"):
            for item in palace_nodes.get(other_domain, []):
                if incident_id in item.get("linked_events", []) or str(first.get("evidence")) in item.get("linked_events", []):
                    palace_links.append(
                        {
                            "source": incident_id,
                            "target": item["event_id"],
                            "relation": "cross_domain_echo",
                            "domain": other_domain,
                        }
                    )

    return {
        "generated_at": utc_now(),
        "domains": list(DOMAINS),
        "palace_nodes": palace_nodes,
        "palace_links": palace_links,
        "node_count": sum(len(items) for items in palace_nodes.values()),
        "link_count": len(palace_links),
        "corrective_actions": "none",
        "recommendations_only": True,
        "sources": {
            "incidents": str(INCIDENT_INDEX.relative_to(ROOT)),
            "patterns": str(INCIDENT_INDEX.relative_to(ROOT)),
            "simulations": str(SIMULATION_JSON.relative_to(ROOT)),
            "dreams": str(DREAM_JSON.relative_to(ROOT)),
            "recalibration_queue": str(QUEUE_JSON.relative_to(ROOT)),
            "self_reflections": str(REFLECTION_MD.relative_to(ROOT)),
        },
    }


def write_palace(palace: dict[str, Any]) -> None:
    PALACE_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# MemPalace",
        "",
        f"- generated_at: {palace['generated_at']}",
        f"- node_count: {palace['node_count']}",
        f"- link_count: {palace['link_count']}",
        "- corrective_actions: none",
        "- response_mode: recommendations only",
        "",
    ]
    for domain in DOMAINS:
        lines.extend([f"## {domain}", ""])
        for item in palace["palace_nodes"].get(domain, []):
            lines.extend(
                [
                    f"- event_id: {item['event_id']}",
                    f"- timestamp: {item['timestamp']}",
                    f"- anomaly_type: {item['anomaly_type']}",
                    f"- confidence: {item['confidence']}",
                    f"- explanation: {item['explanation']}",
                    f"- linked_events: {stable_json(item['linked_events'])}",
                    f"- lessons: {stable_json(item['lessons'])}",
                    "",
                ]
            )
    lines.extend(["## Links", ""])
    for link in palace["palace_links"]:
        lines.append(f"- {stable_json(link)}")
    lines.extend(["", "## Sources", ""])
    for key, value in palace["sources"].items():
        lines.append(f"- {key}: {value}")
    PALACE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    PALACE_JSON.write_text(json.dumps(palace, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_palace_build() -> dict[str, Any]:
    palace = build_palace()
    write_palace(palace)
    build_system_state()
    record_checksum(PALACE_MD, "mem_palace_write", {"source": "incidents_simulations_dreams_queue_reflections"})
    record_checksum(PALACE_JSON, "mem_palace_index_write", {"source": "incidents_simulations_dreams_queue_reflections"})
    summary = {
        "palace": str(PALACE_MD.relative_to(ROOT)),
        "palace_json": str(PALACE_JSON.relative_to(ROOT)),
        "node_count": palace["node_count"],
        "link_count": palace["link_count"],
        "recommendations_only": True,
    }
    append_memory(stable_json(summary), ["tools", "mempalace", "night26"], "mem_palace")
    log_action("mem-palace:build", "completed", "ALLOW", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the MemPalace spatial episodic memory.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(run_palace_build()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
