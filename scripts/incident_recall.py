#!/usr/bin/env python3
"""Build searchable episodic memory from Guardian Reflex incidents."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, stable_json
from remember import append_memory


ROOT = Path(__file__).resolve().parents[1]
INCIDENT_DIR = ROOT / "guardian" / "incidents"
REFLEX_LOG = ROOT / "guardian" / "reflex.jsonl"
DMN_FILE = ROOT / "memory" / "dmn.jsonl"
INDEX_FILE = INCIDENT_DIR / "index.json"
TIMELINE_FILE = INCIDENT_DIR / "timeline.md"
PATTERNS_FILE = INCIDENT_DIR / "patterns.json"

SEVERITY_RANK = {
    "info": 0,
    "warning": 1,
    "critical": 2,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            records.append(json.loads(line))
    return records


def first_matching(pattern: str, text: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def extract_inputs_json(text: str) -> dict[str, Any]:
    match = re.search(r"## Inputs\s+```json\n(.*?)\n```", text, re.DOTALL)
    if not match:
        return {}
    return json.loads(match.group(1))


def parse_anomaly_sections(text: str) -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []
    for match in re.finditer(r"^### ([^\n]+)\n\n(.*?)(?=^### |\Z)", text, re.MULTILINE | re.DOTALL):
        body = match.group(2)
        evidence_raw = first_matching(r"^- evidence: `(.+)`$", body)
        evidence: Any = evidence_raw
        if evidence_raw:
            try:
                evidence = json.loads(evidence_raw)
            except json.JSONDecodeError:
                evidence = evidence_raw
        anomalies.append(
            {
                "rule": match.group(1).strip(),
                "severity": first_matching(r"^- severity: (.+)$", body) or "info",
                "confidence": parse_float(first_matching(r"^- confidence: (.+)$", body)),
                "confidence_class": first_matching(r"^- confidence_class: (.+)$", body),
                "true_anomaly": parse_bool(first_matching(r"^- true_anomaly: (.+)$", body)),
                "scoring_artifact": parse_bool(first_matching(r"^- scoring_artifact: (.+)$", body)),
                "recommendation": first_matching(r"^- recommendation: (.+)$", body),
                "evidence": evidence,
            }
        )
    return anomalies


def parse_float(value: str) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_bool(value: str) -> bool | None:
    lowered = value.casefold()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return None


def telemetry_paths_from_record(record: dict[str, Any]) -> list[str]:
    paths: set[str] = set()
    for key in ("extra_telemetry",):
        value = record.get(key)
        if isinstance(value, str) and value.startswith("observability/snapshots/"):
            paths.add(value)
    for anomaly in record.get("anomalies", []):
        evidence = anomaly.get("evidence")
        if isinstance(evidence, str) and evidence.startswith("observability/snapshots/"):
            paths.add(evidence)
        if isinstance(evidence, list):
            paths.update(item for item in evidence if isinstance(item, str) and item.startswith("observability/snapshots/"))
        if isinstance(evidence, dict):
            paths.update(
                value
                for value in evidence.values()
                if isinstance(value, str) and value.startswith("observability/snapshots/")
            )
    return sorted(paths)


def dmn_links_for_paths(paths: list[str]) -> dict[str, list[dict[str, str]]]:
    links: dict[str, list[dict[str, str]]] = {path: [] for path in paths}
    for line_number, record in enumerate(load_jsonl(DMN_FILE), start=1):
        content = str(record.get("content", ""))
        for path in paths:
            if path in content:
                links[path].append(
                    {
                        "dmn_line": str(line_number),
                        "timestamp": str(record.get("timestamp", "")),
                        "source": str(record.get("source", "")),
                    }
                )
    return links


def parse_incident_notes() -> list[dict[str, Any]]:
    reflex_by_incident = {record.get("incident"): record for record in load_jsonl(REFLEX_LOG)}
    incidents: list[dict[str, Any]] = []
    for path in sorted(INCIDENT_DIR.glob("incident-*.md")):
        text = path.read_text(encoding="utf-8")
        relative = str(path.relative_to(ROOT))
        reflex_record = reflex_by_incident.get(relative, {})
        anomalies = reflex_record.get("anomalies") or parse_anomaly_sections(text)
        telemetry_paths = telemetry_paths_from_record({**reflex_record, "anomalies": anomalies})
        inputs = extract_inputs_json(text)
        if not telemetry_paths and isinstance(inputs.get("latest_telemetry"), dict):
            latest_path = inputs["latest_telemetry"].get("_path")
            if latest_path:
                telemetry_paths.append(latest_path)
        incident = {
            "incident": relative,
            "timestamp": reflex_record.get("timestamp") or first_matching(r"^- timestamp: (.+)$", text),
            "policy": reflex_record.get("policy") or first_matching(r"^- policy: (.+)$", text),
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "telemetry_snapshots": sorted(set(telemetry_paths)),
            "dmn_links": {},
            "extra_telemetry": reflex_record.get("extra_telemetry") or first_matching(r"^- extra_telemetry: (.+)$", text),
            "screenshot": reflex_record.get("screenshot") or first_matching(r"^- screenshot: (.+)$", text),
            "recommendations": sorted({item.get("recommendation", "") for item in anomalies if item.get("recommendation")}),
        }
        incident["dmn_links"] = dmn_links_for_paths(incident["telemetry_snapshots"])
        incidents.append(incident)
    return incidents


def severity_for_incident(incident: dict[str, Any]) -> str:
    severities = [str(item.get("severity", "info")) for item in incident.get("anomalies", [])]
    if not severities:
        return "info"
    return max(severities, key=lambda value: SEVERITY_RANK.get(value, 0))


def build_patterns(incidents: list[dict[str, Any]]) -> dict[str, Any]:
    rule_counts: Counter[str] = Counter()
    severity_by_rule: dict[str, list[str]] = defaultdict(list)
    confidence_classes: Counter[str] = Counter()
    for incident in incidents:
        for anomaly in incident.get("anomalies", []):
            rule = str(anomaly.get("rule", "unknown"))
            rule_counts[rule] += 1
            severity_by_rule[rule].append(str(anomaly.get("severity", "info")))
            confidence_class = anomaly.get("confidence_class")
            if confidence_class:
                confidence_classes[str(confidence_class)] += 1

    latest = incidents[-1] if incidents else None
    latest_severity = severity_for_incident(latest) if latest else "info"
    previous = incidents[:-1]
    previous_max = "none"
    comparison = "no previous incidents"
    if previous:
        previous_max = max((severity_for_incident(item) for item in previous), key=lambda value: SEVERITY_RANK.get(value, 0))
        latest_rank = SEVERITY_RANK.get(latest_severity, 0)
        previous_rank = SEVERITY_RANK.get(previous_max, 0)
        if latest_rank > previous_rank:
            comparison = "latest incident is more severe than previous maximum"
        elif latest_rank < previous_rank:
            comparison = "latest incident is less severe than previous maximum"
        else:
            comparison = "latest incident severity matches previous maximum"

    repeated = {rule: count for rule, count in sorted(rule_counts.items()) if count > 1}
    return {
        "generated_at": utc_now(),
        "incident_count": len(incidents),
        "rule_counts": dict(sorted(rule_counts.items())),
        "repeated_anomaly_types": repeated,
        "severity_by_rule": dict(sorted(severity_by_rule.items())),
        "confidence_classes": dict(sorted(confidence_classes.items())),
        "latest_incident": latest.get("incident") if latest else None,
        "latest_severity": latest_severity,
        "previous_max_severity": previous_max,
        "severity_comparison": comparison,
        "recommendations_only": True,
    }


def write_index(incidents: list[dict[str, Any]], patterns: dict[str, Any]) -> None:
    INDEX_FILE.write_text(
        json.dumps(
            {
                "generated_at": utc_now(),
                "incident_count": len(incidents),
                "incidents": incidents,
                "patterns": patterns,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    PATTERNS_FILE.write_text(json.dumps(patterns, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_timeline(incidents: list[dict[str, Any]], patterns: dict[str, Any]) -> None:
    lines = [
        "# Guardian Incident Timeline",
        "",
        f"- generated_at: {utc_now()}",
        f"- incident_count: {len(incidents)}",
        f"- latest_severity: {patterns['latest_severity']}",
        f"- severity_comparison: {patterns['severity_comparison']}",
        f"- repeated_anomaly_types: {stable_json(patterns['repeated_anomaly_types'])}",
        f"- confidence_classes: {stable_json(patterns.get('confidence_classes', {}))}",
        "- corrective_actions: none",
        "- response_mode: recommendations only",
        "",
        "## Events",
        "",
    ]
    if not incidents:
        lines.append("No incidents indexed.")
    for incident in incidents:
        rules = ", ".join(item.get("rule", "unknown") for item in incident.get("anomalies", [])) or "none"
        lines.extend(
            [
                f"### {incident['timestamp']}",
                "",
                f"- incident: {incident['incident']}",
                f"- severity: {severity_for_incident(incident)}",
                f"- anomaly_rules: {rules}",
                f"- confidence_classes: {stable_json(Counter(str(item.get('confidence_class')) for item in incident.get('anomalies', []) if item.get('confidence_class')))}",
                f"- telemetry_snapshots: {', '.join(incident['telemetry_snapshots']) or 'none'}",
                f"- screenshot: {incident.get('screenshot') or 'none'}",
                "- recommendations:",
            ]
        )
        recommendations = incident.get("recommendations") or ["No action recommended."]
        for recommendation in recommendations:
            lines.append(f"  - {recommendation}")
        lines.append("")
    TIMELINE_FILE.write_text("\n".join(lines), encoding="utf-8")


def run_recall() -> dict[str, Any]:
    INCIDENT_DIR.mkdir(parents=True, exist_ok=True)
    incidents = parse_incident_notes()
    patterns = build_patterns(incidents)
    write_index(incidents, patterns)
    write_timeline(incidents, patterns)
    memory = {
        "index": str(INDEX_FILE.relative_to(ROOT)),
        "timeline": str(TIMELINE_FILE.relative_to(ROOT)),
        "patterns": str(PATTERNS_FILE.relative_to(ROOT)),
        "incident_count": len(incidents),
        "repeated_anomaly_types": patterns["repeated_anomaly_types"],
        "severity_comparison": patterns["severity_comparison"],
        "recommendations_only": True,
    }
    append_memory(stable_json(memory), ["guardian", "incident-recall", "night7"], "incident_recall")
    log_action("incident:recall", "completed", "ALLOW", memory)
    return memory


def main() -> int:
    parser = argparse.ArgumentParser(description="Index and recall Guardian incident patterns.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(run_recall()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
