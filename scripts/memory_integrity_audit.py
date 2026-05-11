#!/usr/bin/env python3
"""Audit local Ambient OS memory and generated observability metadata."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, record_checksum, stable_json, verify_checksum_chain
from remember import validate_memory_file, append_memory


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "guardian" / "audits"
AUDIT_MD = AUDIT_DIR / "memory_integrity_audit.md"
AUDIT_JSON = AUDIT_DIR / "memory_integrity_audit.json"
INCIDENT_DIR = ROOT / "guardian" / "incidents"
INCIDENT_INDEX = INCIDENT_DIR / "index.json"
BASELINE_JSON = ROOT / "guardian" / "baselines" / "telemetry_baseline.json"
BASELINE_REPORT = ROOT / "guardian" / "baselines" / "baseline_report.md"
HEALTH_JSON = ROOT / "guardian" / "health" / "health_scores.json"
DASHBOARD_HTML = ROOT / "dashboard" / "index.html"
DAILY_DIGEST = ROOT / "dashboard" / "daily_digest.md"
DMN_FILE = ROOT / "memory" / "dmn.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def dmn_count() -> int:
    if not DMN_FILE.exists():
        return 0
    with DMN_FILE.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def issue(status: str, check: str, detail: str) -> dict[str, str]:
    return {"status": status, "check": check, "detail": detail}


def parse_markdown_kv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^- ([^:]+): (.*)$", line)
        if match:
            values[match.group(1).strip()] = match.group(2).strip()
    return values


def parse_baseline_table() -> dict[str, dict[str, str]]:
    if not BASELINE_REPORT.exists():
        return {}
    rows: dict[str, dict[str, str]] = {}
    for line in BASELINE_REPORT.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| Metric ") or line.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 9:
            continue
        rows[cells[0]] = {
            "current": cells[1],
            "mean": cells[2],
            "min": cells[3],
            "max": cells[4],
            "stddev": cells[5],
            "rolling_mean": cells[6],
            "severity": cells[7],
            "incident_links": cells[8],
        }
    return rows


def html_value(label: str) -> str:
    if not DASHBOARD_HTML.exists():
        return ""
    text = DASHBOARD_HTML.read_text(encoding="utf-8")
    patterns = [
        rf'<div class="label">{re.escape(label)}</div>\s*<div class="value[^"]*">([^<]+)</div>',
        rf"<tr><th>{re.escape(label)}</th><td(?:><code>|>)([^<]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ""


def audit_dmn_and_logs(results: list[dict[str, str]]) -> None:
    validation = validate_memory_file()
    if validation.get("ok"):
        results.append(issue("ok", "dmn_schema", f"{validation.get('records')} records valid"))
    else:
        results.append(issue("error", "dmn_schema", stable_json(validation)))

    chain_ok, message = verify_checksum_chain()
    results.append(issue("ok" if chain_ok else "error", "action_log_checksum_chain", message))


def audit_incidents(results: list[dict[str, str]]) -> dict[str, Any]:
    index = load_json(INCIDENT_INDEX)
    indexed = [item.get("incident") for item in index.get("incidents", [])]
    duplicates = sorted(path for path, count in Counter(indexed).items() if path and count > 1)
    notes = sorted(str(path.relative_to(ROOT)) for path in INCIDENT_DIR.glob("incident-*.md"))
    missing_notes = sorted(path for path in indexed if path and not (ROOT / path).exists())
    orphan_notes = sorted(path for path in notes if path not in indexed)
    missing_refs: list[str] = []
    for incident in index.get("incidents", []):
        for key in ("extra_telemetry", "screenshot"):
            value = incident.get(key)
            if isinstance(value, str) and value != "none" and not (ROOT / value).exists():
                missing_refs.append(f"{incident.get('incident')} -> {value}")
        for path in incident.get("telemetry_snapshots", []):
            if not (ROOT / path).exists():
                missing_refs.append(f"{incident.get('incident')} -> {path}")

    results.append(issue("ok" if not missing_notes else "error", "incident_index_links", f"missing_notes={missing_notes or 'none'}"))
    results.append(issue("ok" if not orphan_notes else "warning", "orphan_incident_notes", f"orphans={orphan_notes or 'none'}"))
    results.append(issue("ok" if not duplicates else "error", "duplicated_incident_ids", f"duplicates={duplicates or 'none'}"))
    results.append(issue("ok" if not missing_refs else "error", "incident_references", f"missing_refs={missing_refs or 'none'}"))
    return {"incident_count": len(indexed), "orphan_notes": orphan_notes, "duplicates": duplicates, "missing_refs": missing_refs}


def audit_health(results: list[dict[str, str]]) -> dict[str, Any]:
    health = load_json(HEALTH_JSON)
    history = health.get("history", [])
    current = health.get("current", {})
    last = history[-1] if history else {}
    checks = {
        "timestamp": current.get("timestamp") == last.get("timestamp"),
        "path": current.get("path") == last.get("path"),
        "health_score": current.get("health_score") == last.get("health_score"),
    }
    ok = bool(history) and all(checks.values())
    results.append(issue("ok" if ok else "error", "health_history_consistency", stable_json(checks)))
    return {"health_score": current.get("health_score"), "trend": health.get("trend"), "history_count": len(history)}


def audit_baseline(results: list[dict[str, str]]) -> None:
    baseline = load_json(BASELINE_JSON)
    report_rows = parse_baseline_table()
    mismatches: list[str] = []
    for metric, data in baseline.get("metrics", {}).items():
        row = report_rows.get(metric)
        if not row:
            mismatches.append(f"{metric}: missing from report")
            continue
        expected = {
            "current": data.get("current"),
            "mean": data.get("baseline", {}).get("mean"),
            "min": data.get("baseline", {}).get("min"),
            "max": data.get("baseline", {}).get("max"),
            "stddev": data.get("baseline", {}).get("stddev"),
            "rolling_mean": data.get("rolling", {}).get("mean"),
            "severity": data.get("deviation", {}).get("severity"),
            "incident_links": len(data.get("incident_links", [])),
        }
        for key, value in expected.items():
            if str(value) != row[key]:
                mismatches.append(f"{metric}.{key}: json={value} report={row[key]}")
    results.append(issue("ok" if not mismatches else "error", "baseline_report_matches_json", "; ".join(mismatches) or "matched"))


def audit_dashboard_and_digest(results: list[dict[str, str]]) -> dict[str, Any]:
    health = load_json(HEALTH_JSON)
    incidents = load_json(INCIDENT_INDEX)
    calibration = load_json(INCIDENT_DIR / "reflex_confidence_calibration.json")
    digest = parse_markdown_kv(DAILY_DIGEST)
    current = health.get("current", {})
    anomaly = (calibration.get("anomalies") or [{}])[-1]
    repeated = incidents.get("patterns", {}).get("repeated_anomaly_types", {})
    expected = {
        "Overall Health": f"{float(current.get('health_score', 0)):.2f}",
        "Trend": str(health.get("trend")),
        "Reflex Confidence": f"{float(anomaly.get('confidence', 0)):.2f}",
        "Incidents": str(incidents.get("incident_count")),
    }
    dashboard_mismatches = []
    for label, value in expected.items():
        observed = html_value(label)
        if observed != value:
            dashboard_mismatches.append(f"{label}: html={observed} source={value}")
    results.append(issue("ok" if not dashboard_mismatches else "error", "dashboard_values_match_source", "; ".join(dashboard_mismatches) or "matched"))

    digest_expected = {
        "health_score": str(current.get("health_score")),
        "trend": str(health.get("trend")),
        "reflex_confidence": str(anomaly.get("confidence")),
        "risk_class": str(anomaly.get("confidence_class")),
        "incident_count": str(incidents.get("incident_count")),
        "repeated_anomaly_count": str(sum(int(value) for value in repeated.values())),
    }
    digest_mismatches = []
    for key, value in digest_expected.items():
        if digest.get(key) != value:
            digest_mismatches.append(f"{key}: digest={digest.get(key)} source={value}")
    digest_count = int(digest.get("dmn_append_count", "0") or 0)
    current_dmn = dmn_count()
    dashboard_count = html_value("DMN Append Count")
    if dashboard_count and digest.get("dmn_append_count") != dashboard_count:
        digest_mismatches.append(f"dmn_append_count: digest={digest.get('dmn_append_count')} dashboard={dashboard_count}")
    if digest_count != current_dmn:
        digest_mismatches.append(f"dmn_append_count: digest={digest_count} current={current_dmn}")
    status = "ok" if not digest_mismatches else "warning"
    detail = "; ".join(digest_mismatches) if digest_mismatches else f"matched; digest_dmn_count={digest_count}, current_dmn_count={current_dmn}"
    results.append(issue(status, "daily_digest_values_match_source", detail))
    return {"current_dmn_count": current_dmn, "digest_dmn_count": digest_count}


def write_report(results: list[dict[str, str]], summary: dict[str, Any]) -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    status_counts = dict(Counter(item["status"] for item in results))
    report = {
        "generated_at": utc_now(),
        "status_counts": status_counts,
        "checks": results,
        "summary": summary,
        "corrective_actions": "none",
        "recommendations_only": True,
    }
    AUDIT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Memory Integrity Audit",
        "",
        f"- generated_at: {report['generated_at']}",
        f"- status_counts: {stable_json(status_counts)}",
        "- corrective_actions: none",
        "- response_mode: recommendations only",
        "",
        "## Checks",
        "",
        "| Status | Check | Detail |",
        "| --- | --- | --- |",
    ]
    for item in results:
        detail = item["detail"].replace("|", "/")
        lines.append(f"| {item['status']} | {item['check']} | {detail} |")
    lines.extend(["", "## Recommendations", ""])
    if status_counts.get("error"):
        lines.append("- Review error checks before expanding automation.")
    if status_counts.get("warning"):
        lines.append("- Regenerate derived dashboard or digest metadata when DMN counts need exact point-in-time alignment.")
    if not status_counts.get("error") and not status_counts.get("warning"):
        lines.append("- No corrective action recommended; continue routine integrity audits.")
    AUDIT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_audit() -> dict[str, Any]:
    results: list[dict[str, str]] = []
    audit_dmn_and_logs(results)
    incident_summary = audit_incidents(results)
    health_summary = audit_health(results)
    audit_baseline(results)
    dashboard_summary = audit_dashboard_and_digest(results)
    summary = {
        "incidents": incident_summary,
        "health": health_summary,
        "dashboard": dashboard_summary,
    }
    write_report(results, summary)
    record_checksum(AUDIT_JSON, "memory_integrity_audit_json")
    record_checksum(AUDIT_MD, "memory_integrity_audit_markdown")
    memory = {
        "audit_report": str(AUDIT_MD.relative_to(ROOT)),
        "checks": len(results),
        "status_counts": dict(Counter(item["status"] for item in results)),
        "recommendations_only": True,
    }
    append_memory(stable_json(memory), ["guardian", "audit", "memory-integrity", "night14"], "memory_integrity_audit")
    log_action("audit:memory-integrity", "completed", "ALLOW", memory)
    return memory


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit local memory integrity.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(run_audit()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
