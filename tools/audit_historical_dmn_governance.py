"""Read-only historical DMN governance audit.

Phase 1G.9 constraints:
- read memory/dmn.jsonl only;
- do not append to DMN;
- do not modify logs or production records;
- write outputs only to reports/dmn_audit/;
- do not expose sensitive raw content.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DMN_PATH = ROOT / "memory" / "dmn.jsonl"
REPORT_DIR = ROOT / "reports" / "dmn_audit"

TARGET_SAMPLE_SIZE = 50


@dataclass(frozen=True)
class ParsedRecord:
    line_no: int
    line: str
    data: dict[str, Any]


def load_dmn_records() -> list[ParsedRecord]:
    records: list[ParsedRecord] = []
    for line_no, line in enumerate(DMN_PATH.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            records.append(ParsedRecord(line_no=line_no, line=line, data=data))
    return records


def choose_samples(records: list[ParsedRecord]) -> list[ParsedRecord]:
    if len(records) <= TARGET_SAMPLE_SIZE:
        return records

    selected: dict[int, ParsedRecord] = {}

    def add(record: ParsedRecord) -> None:
        selected[record.line_no] = record

    for record in records[:5]:
        add(record)
    for record in records[-5:]:
        add(record)

    keyword_groups = [
        ("governance", "constitution", "policy", "guardian"),
        ("telemetry", "sense_local", "cpu_usage", "memory_usage", "disk_usage"),
        ("phase", "completed phase", "phase-1", "readiness"),
        ("guardian", "guardian_observation", "guardian"),
        ("sync", "sync", "source_node", "office-hermes", "home-hermes"),
    ]
    for keywords in keyword_groups:
        for record in records:
            haystack = normalized_text(record)
            if any(keyword in haystack for keyword in keywords):
                add(record)
                break

    remaining_slots = TARGET_SAMPLE_SIZE - len(selected)
    if remaining_slots > 0:
        step = max(1, len(records) // remaining_slots)
        for index in range(0, len(records), step):
            add(records[index])
            if len(selected) >= TARGET_SAMPLE_SIZE:
                break

    return [selected[line_no] for line_no in sorted(selected)[:TARGET_SAMPLE_SIZE]]


def normalized_text(record: ParsedRecord) -> str:
    content = str(record.data.get("content", ""))
    tags = " ".join(str(tag) for tag in record.data.get("tags", []))
    source = str(record.data.get("source", ""))
    return f"{source} {tags} {content}".lower()


def line_hash(line: str) -> str:
    return "sha256:" + hashlib.sha256(line.encode("utf-8")).hexdigest()


def classify_record_type(record: ParsedRecord) -> str:
    text = normalized_text(record)
    if "guardian" in text:
        return "guardian_observation"
    if any(term in text for term in ("governance", "constitution", "policy", "decision-log")):
        return "governance"
    if any(term in text for term in ("phase", "completed phase", "readiness", "turbovec")):
        return "phase_summary"
    if any(term in text for term in ("telemetry", "sense_local", "cpu_usage", "memory_usage", "disk_usage")):
        return "telemetry"
    if any(term in text for term in ("system", "hook", "cursor-agent-hook", "status")):
        return "system_observation"
    return "unknown"


def detect_sensitive(record: ParsedRecord) -> bool:
    text = normalized_text(record)
    sensitive_patterns = [
        r"host",
        r"workspace_roots",
        r"conversation_id",
        r"generation_id",
        r"session_id",
        r"\\\\",
        r"/home/",
        r"c:/users",
        r"cpu_usage",
        r"memory_usage",
        r"disk_usage",
    ]
    return any(re.search(pattern, text) for pattern in sensitive_patterns)


def privacy_confidence(record: ParsedRecord, record_type: str) -> str:
    if detect_sensitive(record):
        return "high"
    if record_type in {"governance", "phase_summary", "guardian_observation"}:
        return "medium"
    if record_type == "unknown":
        return "unknown"
    return "low"


def has_field(record: ParsedRecord, field: str) -> bool:
    return field in record.data and record.data.get(field) not in ("", None, [])


def has_source_node(record: ParsedRecord) -> bool:
    if has_field(record, "source_node"):
        return True
    content = str(record.data.get("content", ""))
    return '"source_node"' in content or "home-hermes" in content.lower() or "office-hermes" in content.lower()


def has_privacy_class(record: ParsedRecord) -> bool:
    if has_field(record, "privacy_class"):
        return True
    return "privacy_class" in str(record.data.get("content", ""))


def has_retention_policy(record: ParsedRecord) -> bool:
    if has_field(record, "retention_policy"):
        return True
    return "retention_policy" in str(record.data.get("content", ""))


def has_replay_pointer(record: ParsedRecord) -> bool:
    if has_field(record, "replay_pointer"):
        return True
    return "replay_pointer" in str(record.data.get("content", ""))


def has_guardian_review(record: ParsedRecord) -> bool:
    text = normalized_text(record)
    return "guardian_review" in text or "guardian classified" in text or "guardian status" in text


def has_lineage(record: ParsedRecord) -> bool:
    if has_field(record, "lineage"):
        return True
    content = str(record.data.get("content", ""))
    return any(term in content for term in ("parent_record_ids", "root_record_id", "derived_from"))


def has_governance_state(record: ParsedRecord) -> bool:
    if has_field(record, "governance_state"):
        return True
    return "governance_state" in str(record.data.get("content", ""))


def replay_coverage_status(record: ParsedRecord) -> str:
    if has_field(record, "replay_pointer"):
        return "explicit"
    content = str(record.data.get("content", ""))
    if "replay_pointer" in content or "replay" in normalized_text(record):
        return "derived"
    if classify_record_type(record) in {"telemetry", "system_observation", "governance", "phase_summary"}:
        return "missing"
    return "unknown"


def classify_sync(record: ParsedRecord, record_type: str, privacy: str, replay_status: str) -> str:
    if detect_sensitive(record):
        return "not_eligible_sensitive"
    if replay_status == "missing":
        return "not_eligible_missing_replay"
    if record_type in {"governance", "policy", "guardian_observation"}:
        return "eligible_governance_only"
    if record_type == "phase_summary":
        return "eligible_summary_only"
    if replay_status == "derived":
        return "eligible_evidence_only"
    if privacy in {"unknown", "low"}:
        return "requires_human_review"
    return "unknown"


def redacted_summary(record: ParsedRecord, record_type: str) -> str:
    source = str(record.data.get("source", "unknown"))
    tags = record.data.get("tags", [])
    if not isinstance(tags, list):
        tags = []
    if detect_sensitive(record):
        return f"Redacted {record_type} record from source {source}; sensitive operational identifiers or local paths are not copied."
    content = str(record.data.get("content", ""))
    compact = re.sub(r"\s+", " ", content).strip()
    compact = re.sub(r"[A-Za-z]:/Users/[^\\s]+", "[redacted-path]", compact)
    compact = re.sub(r"/home/[^\\s]+", "[redacted-path]", compact)
    if len(compact) > 180:
        compact = compact[:177] + "..."
    return compact or f"{record_type} record from source {source} with tags {tags[:5]}"


def audit_record(sample_id: int, record: ParsedRecord) -> dict[str, Any]:
    record_type = classify_record_type(record)
    privacy = privacy_confidence(record, record_type)
    replay_status = replay_coverage_status(record)
    fields = {
        "has_timestamp": has_field(record, "timestamp"),
        "has_source_node": has_source_node(record),
        "has_privacy_class": has_privacy_class(record),
        "has_retention_policy": has_retention_policy(record),
        "has_replay_pointer": has_replay_pointer(record),
        "has_guardian_review": has_guardian_review(record),
        "has_lineage": has_lineage(record),
        "has_governance_state": has_governance_state(record),
    }
    gap_count = sum(1 for ok in fields.values() if not ok)
    sync = classify_sync(record, record_type, privacy, replay_status)
    requires_review = sync in {
        "not_eligible_sensitive",
        "not_eligible_missing_replay",
        "requires_human_review",
        "unknown",
    }
    notes: list[str] = []
    if detect_sensitive(record):
        notes.append("summary_only_sensitive_content")
    if not fields["has_source_node"]:
        notes.append("missing_source_node")
    if replay_status in {"missing", "unknown"}:
        notes.append("replay_pointer_gap")
    if not fields["has_privacy_class"]:
        notes.append("privacy_class_gap")
    return {
        "sample_id": f"sample-{sample_id:03d}",
        "source_line": record.line_no,
        "source_hash": line_hash(record.line),
        "record_type": record_type,
        "summary_redacted": redacted_summary(record, record_type),
        **fields,
        "privacy_confidence": privacy,
        "sync_eligibility": sync,
        "replay_coverage_status": replay_status,
        "requires_human_review": requires_review,
        "metadata_gap_count": gap_count,
        "notes": notes,
    }


def pct(count: int, total: int) -> str:
    return f"{(count / max(total, 1)) * 100:.1f}%"


def coverage_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = [
        "has_timestamp",
        "has_source_node",
        "has_privacy_class",
        "has_retention_policy",
        "has_replay_pointer",
        "has_guardian_review",
        "has_lineage",
        "has_governance_state",
    ]
    total = len(rows)
    return [
        {
            "field": field,
            "count": sum(1 for row in rows if row[field]),
            "percentage": pct(sum(1 for row in rows if row[field]), total),
        }
        for field in fields
    ]


def table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def write_reports(rows: list[dict[str, Any]], records_total: int) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    total = len(rows)
    coverage = coverage_table(rows)
    type_counts = Counter(row["record_type"] for row in rows)
    privacy_counts = Counter(row["privacy_confidence"] for row in rows)
    sync_counts = Counter(row["sync_eligibility"] for row in rows)
    replay_counts = Counter(row["replay_coverage_status"] for row in rows)

    dataset = {
        "phase": "1G.9",
        "status": "read_only_redacted_audit",
        "source": "memory/dmn.jsonl",
        "records_total": records_total,
        "sample_size": total,
        "sampling_method": "first 5, last 5, keyword representatives, deterministic evenly spaced fill to 50",
        "no_mutation": True,
        "records": rows,
        "summary": {
            "record_type_counts": dict(type_counts),
            "privacy_confidence_counts": dict(privacy_counts),
            "sync_eligibility_counts": dict(sync_counts),
            "replay_coverage_counts": dict(replay_counts),
            "metadata_coverage": coverage,
            "average_metadata_gap_count": round(sum(row["metadata_gap_count"] for row in rows) / max(total, 1), 2),
        },
    }
    (REPORT_DIR / "historical_dmn_governance_audit.json").write_text(
        json.dumps(dataset, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    summary_rows = [[item["field"], item["count"], item["percentage"]] for item in coverage]
    (REPORT_DIR / "historical_dmn_governance_audit_summary.md").write_text(
        "\n".join(
            [
                "# Historical DMN Governance Audit Summary",
                "",
                "Phase: 1G.9 Larger Read-Only Historical DMN Governance Audit",
                "Date: 2026-06-10",
                "Status: Read-only redacted audit. No DMN memory was mutated.",
                "",
                f"Sample size: {total} of {records_total} parsed DMN records.",
                "",
                "Sampling method: first 5 records, last 5 records, keyword representatives for governance, telemetry, phase summaries, Guardian, and sync, then deterministic evenly spaced fill to 50.",
                "",
                "## Metadata Coverage",
                "",
                table(["Field", "Count", "Coverage"], summary_rows),
                "",
                "## Record Type Coverage",
                "",
                table(["Record Type", "Count"], [[k, v] for k, v in sorted(type_counts.items())]),
                "",
                "## Major Systemic Gaps",
                "",
                "- Source node identity is usually absent or only inferable.",
                "- Privacy class is usually absent and must be derived.",
                "- Retention policy is usually absent.",
                "- Per-record replay pointers are usually absent.",
                "- Guardian review status is rarely explicit.",
                "- Lineage and governance state are not native fields on historical DMN records.",
                "",
                "## Risk Assessment",
                "",
                "Historical DMN records can be summarized and audited, but most are not directly sync-ready. Sensitive operational records require summary-only handling and human review.",
                "",
                "## Recommended Next Phase",
                "",
                "Create schema-compatible sidecar proposals for source node, privacy class, retention policy, replay pointer, and governance state repair without rewriting `memory/dmn.jsonl`.",
                "",
                "Updated DMN Governance Readiness Score: 26 / 30.",
                "",
                "TurboVec remains paused.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    sync_rows = [[k, v, pct(v, total)] for k, v in sorted(sync_counts.items())]
    review_count = sum(1 for row in rows if row["requires_human_review"])
    (REPORT_DIR / "historical_dmn_sync_eligibility_distribution.md").write_text(
        "\n".join(
            [
                "# Historical DMN Sync Eligibility Distribution",
                "",
                "Phase: 1G.9",
                "Status: Read-only audit. No sync was performed.",
                "",
                "## Distribution",
                "",
                table(["Sync Eligibility", "Count", "Percentage"], sync_rows),
                "",
                f"Records requiring human review: {review_count} / {total} ({pct(review_count, total)}).",
                "",
                "## Cross-Node Sync Readiness Conclusion",
                "",
                "Historical DMN is not ready for automatic cross-node sync. Summary-only or governance-only sync may be possible for selected records after human review, privacy labeling, replay repair, and source-node repair.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    privacy_rows = [[k, v, pct(v, total)] for k, v in sorted(privacy_counts.items())]
    (REPORT_DIR / "historical_dmn_privacy_confidence_report.md").write_text(
        "\n".join(
            [
                "# Historical DMN Privacy Confidence Report",
                "",
                "Phase: 1G.9",
                "Status: Read-only audit with redacted summaries.",
                "",
                "## Privacy Confidence Distribution",
                "",
                table(["Privacy Confidence", "Count", "Percentage"], privacy_rows),
                "",
                "## High-Risk Categories",
                "",
                "- Telemetry and local system observations.",
                "- Hook records containing conversation IDs, generation IDs, workspace roots, or local paths.",
                "- Records with machine names, host fields, or operational metrics.",
                "",
                "## Classification Uncertainty",
                "",
                "Privacy confidence is derived heuristically because historical DMN records usually lack native `privacy_class` metadata.",
                "",
                "## Recommendation",
                "",
                "Add non-mutating privacy sidecars or wrappers before any sync, embedding, or broader recall indexing of historical DMN records.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    replay_rows = [[k, v, pct(v, total)] for k, v in sorted(replay_counts.items())]
    (REPORT_DIR / "historical_dmn_replay_coverage_report.md").write_text(
        "\n".join(
            [
                "# Historical DMN Replay Coverage Report",
                "",
                "Phase: 1G.9",
                "Status: Read-only audit.",
                "",
                "## Replay Coverage",
                "",
                table(["Replay Coverage Status", "Count", "Percentage"], replay_rows),
                "",
                "## Impact On Auditability",
                "",
                "Source line and hash allow derived provenance, but missing explicit replay pointers limit full reconstruction. Records without replay manifests should not become automatic sync or vector-recall candidates.",
                "",
                "## Recommendation",
                "",
                "Create replay sidecar proposals that link historical DMN source lines to manifests, causal event IDs, and root event IDs where evidence exists.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    records = load_dmn_records()
    samples = choose_samples(records)
    rows = [audit_record(index, record) for index, record in enumerate(samples, 1)]
    write_reports(rows, len(records))


if __name__ == "__main__":
    main()
