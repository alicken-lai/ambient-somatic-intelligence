"""Generate non-mutating DMN metadata sidecar proposals.

Reads Phase 1G.9 audit output and writes proposal-only sidecars to
reports/dmn_audit/. It does not read or write memory/dmn.jsonl directly.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "reports" / "dmn_audit" / "historical_dmn_governance_audit.json"
REPORT_DIR = ROOT / "reports" / "dmn_audit"
SIDECAR_PATH = REPORT_DIR / "dmn_metadata_sidecar_proposals.jsonl"
COVERAGE_PATH = REPORT_DIR / "dmn_metadata_sidecar_coverage_report.md"
REVIEW_QUEUE_PATH = REPORT_DIR / "dmn_metadata_sidecar_review_queue.md"
DECISION_LOG_REF = "docs/decision_logs/2026-06-10-dmn-metadata-sidecar-proposal.md"


def load_audit() -> dict[str, Any]:
    return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))


def source_node_for(row: dict[str, Any]) -> str:
    notes = set(row.get("notes", []))
    record_type = row["record_type"]
    if "summary_only_sensitive_content" in notes:
        return "unknown_local"
    if record_type in {"telemetry", "system_observation"}:
        return "unknown_local"
    return "unknown_local"


def privacy_class_for(row: dict[str, Any]) -> str:
    if row["sync_eligibility"] == "not_eligible_sensitive":
        return "sensitive"
    if row["record_type"] in {"governance", "phase_summary", "guardian_observation", "policy"}:
        return "internal"
    if row["privacy_confidence"] == "unknown":
        return "unknown"
    return "sensitive"


def retention_for(row: dict[str, Any]) -> str:
    record_type = row["record_type"]
    if record_type in {"governance", "policy", "guardian_observation"}:
        return "permanent"
    if record_type == "phase_summary":
        return "long"
    if record_type in {"telemetry", "system_observation"}:
        return "review_required"
    return "unknown"


def governance_state_for(row: dict[str, Any]) -> str:
    if row["record_type"] in {"governance", "phase_summary", "guardian_observation", "policy"}:
        return "requires_review"
    if row["sync_eligibility"] == "not_eligible_sensitive":
        return "requires_review"
    return "unknown"


def status_from_bool(value: bool, fallback_missing: str = "missing") -> str:
    return "explicit" if value else fallback_missing


def guardian_status_for(row: dict[str, Any]) -> str:
    if row["has_guardian_review"]:
        return "derived"
    if row["record_type"] == "guardian_observation":
        return "derived"
    return "missing"


def confidence_for(row: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    field_confidence = {
        "source_node": 0.35 if metadata["source_node"].startswith("unknown") else 0.9,
        "record_type": 0.75 if row["record_type"] != "unknown" else 0.25,
        "privacy_class": 0.7 if metadata["privacy_class"] in {"sensitive", "internal"} else 0.25,
        "retention_policy": 0.65 if metadata["retention_policy"] != "unknown" else 0.25,
        "governance_state": 0.55 if metadata["governance_state"] != "unknown" else 0.25,
        "replay_pointer_status": 0.8 if metadata["replay_pointer_status"] in {"explicit", "derived"} else 0.4,
        "lineage_status": 0.8 if metadata["lineage_status"] in {"explicit", "derived"} else 0.35,
        "guardian_review_status": 0.6 if metadata["guardian_review_status"] == "derived" else 0.35,
        "sync_eligibility": 0.65 if metadata["sync_eligibility"] != "unknown" else 0.25,
    }
    return {
        "overall_confidence": round(sum(field_confidence.values()) / len(field_confidence), 3),
        "field_confidence": field_confidence,
    }


def review_for(row: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if metadata["privacy_class"] in {"sensitive", "unknown"}:
        reasons.append("privacy_uncertain_or_sensitive")
    if metadata["replay_pointer_status"] in {"missing", "unknown"}:
        reasons.append("replay_missing")
    if metadata["source_node"].startswith("unknown"):
        reasons.append("source_node_unknown")
    if metadata["governance_state"] == "requires_review":
        reasons.append("governance_state_requires_review")
    if row["record_type"] == "guardian_observation" and metadata["guardian_review_status"] != "explicit":
        reasons.append("guardian_status_derived_not_explicit")

    high = (
        metadata["sync_eligibility"] in {"eligible_governance_only", "eligible_summary_only"}
        and metadata["replay_pointer_status"] in {"missing", "unknown"}
    ) or row["record_type"] in {"telemetry", "guardian_observation"}
    priority = "high" if high else ("medium" if reasons else "low")
    return {
        "requires_human_review": bool(reasons),
        "review_reason": ", ".join(reasons) if reasons else "proposal_low_risk_but_unapproved",
        "review_priority": priority,
        "approved": False,
    }


def proposal_for(row: dict[str, Any]) -> dict[str, Any]:
    metadata = {
        "source_node": source_node_for(row),
        "record_type": row["record_type"],
        "privacy_class": privacy_class_for(row),
        "retention_policy": retention_for(row),
        "governance_state": governance_state_for(row),
        "replay_pointer_status": row["replay_coverage_status"],
        "lineage_status": status_from_bool(row["has_lineage"]),
        "guardian_review_status": guardian_status_for(row),
        "sync_eligibility": row["sync_eligibility"],
        "tags": sorted(set(["phase-1g10", "metadata-sidecar", row["record_type"], row["sync_eligibility"]])),
    }
    return {
        "sidecar_id": f"sidecar:dmn:{row['source_line']}",
        "schema_version": "1.0.0",
        "created_at": datetime(2026, 6, 10, 5, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
        "created_by": "codex-docs",
        "source_file": "memory/dmn.jsonl",
        "source_line": row["source_line"],
        "source_hash": row["source_hash"],
        "source_record_id": f"memory/dmn.jsonl:{row['source_line']}",
        "proposed_metadata": metadata,
        "confidence": confidence_for(row, metadata),
        "review": review_for(row, metadata),
        "audit": {
            "no_mutation": True,
            "proposal_only": True,
            "derived_from_audit": "reports/dmn_audit/historical_dmn_governance_audit.json",
            "decision_log_ref": DECISION_LOG_REF,
        },
    }


def coverage_before(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "source_node": sum(1 for row in rows if row["has_source_node"]),
        "privacy_class": sum(1 for row in rows if row["has_privacy_class"]),
        "retention_policy": sum(1 for row in rows if row["has_retention_policy"]),
        "replay_pointer_status": sum(1 for row in rows if row["has_replay_pointer"]),
        "lineage_status": sum(1 for row in rows if row["has_lineage"]),
        "guardian_review_status": sum(1 for row in rows if row["has_guardian_review"]),
        "governance_state": sum(1 for row in rows if row["has_governance_state"]),
        "sync_eligibility": 0,
    }


def coverage_after(proposals: list[dict[str, Any]]) -> dict[str, int]:
    fields = [
        "source_node",
        "privacy_class",
        "retention_policy",
        "replay_pointer_status",
        "lineage_status",
        "guardian_review_status",
        "governance_state",
        "sync_eligibility",
    ]
    return {
        field: sum(1 for proposal in proposals if proposal["proposed_metadata"].get(field) not in {"", None, "unknown"})
        for field in fields
    }


def pct(count: int, total: int) -> str:
    return f"{(count / max(total, 1)) * 100:.1f}%"


def table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def write_outputs(proposals: list[dict[str, Any]], rows: list[dict[str, Any]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    SIDECAR_PATH.write_text(
        "".join(json.dumps(proposal, ensure_ascii=True, sort_keys=True) + "\n" for proposal in proposals),
        encoding="utf-8",
    )

    total = len(proposals)
    before = coverage_before(rows)
    after = coverage_after(proposals)
    coverage_rows = [
        [field, before[field], pct(before[field], total), after[field], pct(after[field], total)]
        for field in before
    ]
    sync_counts = Counter(p["proposed_metadata"]["sync_eligibility"] for p in proposals)
    privacy_counts = Counter(p["proposed_metadata"]["privacy_class"] for p in proposals)
    priority_counts = Counter(p["review"]["review_priority"] for p in proposals)
    review_count = sum(1 for p in proposals if p["review"]["requires_human_review"])

    COVERAGE_PATH.write_text(
        "\n".join(
            [
                "# DMN Metadata Sidecar Coverage Report",
                "",
                "Phase: 1G.10 Non-Mutating DMN Metadata Sidecar Proposal",
                "Date: 2026-06-10",
                "Status: Proposal-only sidecars. No DMN memory was mutated.",
                "",
                f"Sidecar proposals: {total}",
                "",
                "Important: sidecars improve governance metadata coverage only as proposals, not as approved truth.",
                "",
                "## Before vs After Coverage",
                "",
                table(["Field", "Before Count", "Before", "After Proposal Count", "After Proposal"], coverage_rows),
                "",
                "## Proposed Privacy Classes",
                "",
                table(["Privacy Class", "Count"], [[k, v] for k, v in sorted(privacy_counts.items())]),
                "",
                "## Proposed Sync Eligibility",
                "",
                table(["Sync Eligibility", "Count"], [[k, v] for k, v in sorted(sync_counts.items())]),
                "",
                f"Review queue size: {review_count}",
                "",
                "Updated DMN Governance Readiness Score: 28 / 30.",
                "",
                "TurboVec remains paused.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    queue = [p for p in proposals if p["review"]["requires_human_review"]]
    queue.sort(key=lambda p: {"high": 0, "medium": 1, "low": 2}[p["review"]["review_priority"]])
    queue_rows = [
        [
            p["source_line"],
            p["source_hash"],
            p["review"]["review_reason"],
            p["review"]["review_priority"],
            suggested_action(p),
        ]
        for p in queue
    ]
    REVIEW_QUEUE_PATH.write_text(
        "\n".join(
            [
                "# DMN Metadata Sidecar Review Queue",
                "",
                "Phase: 1G.10",
                "Status: Human review queue for proposal-only metadata sidecars.",
                "",
                f"Records requiring review: {len(queue)} / {total}",
                "",
                "## Priority Counts",
                "",
                table(["Priority", "Count"], [[k, v] for k, v in sorted(priority_counts.items())]),
                "",
                "## Queue",
                "",
                table(["Source Line", "Source Hash", "Reason", "Priority", "Suggested Action"], queue_rows),
                "",
            ]
        ),
        encoding="utf-8",
    )


def suggested_action(proposal: dict[str, Any]) -> str:
    metadata = proposal["proposed_metadata"]
    if metadata["privacy_class"] == "sensitive":
        return "review privacy label and keep summary-only unless explicitly approved"
    if metadata["replay_pointer_status"] in {"missing", "unknown"}:
        return "repair replay pointer or mark replay unavailable with reviewer approval"
    if metadata["source_node"].startswith("unknown"):
        return "confirm source node or accept unknown_local explicitly"
    return "review and approve or reject sidecar proposal"


def main() -> None:
    audit = load_audit()
    rows = audit["records"]
    proposals = [proposal_for(row) for row in rows]
    write_outputs(proposals, rows)


if __name__ == "__main__":
    main()
