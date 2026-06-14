import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "dmn_audit"
AUDIT_JSON = REPORT_DIR / "historical_dmn_governance_audit.json"


def run_audit() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "audit_historical_dmn_governance.py")],
        cwd=ROOT,
        check=True,
    )


def load_audit() -> dict:
    return json.loads(AUDIT_JSON.read_text(encoding="utf-8"))


def test_audit_generates_required_outputs() -> None:
    run_audit()
    required = [
        "historical_dmn_governance_audit.json",
        "historical_dmn_governance_audit_summary.md",
        "historical_dmn_sync_eligibility_distribution.md",
        "historical_dmn_privacy_confidence_report.md",
        "historical_dmn_replay_coverage_report.md",
    ]
    for name in required:
        assert (REPORT_DIR / name).exists()


def test_audit_dataset_shape_and_sample_size() -> None:
    run_audit()
    data = load_audit()
    assert data["no_mutation"] is True
    assert 20 <= data["sample_size"] <= 50
    assert len(data["records"]) == data["sample_size"]

    required_fields = {
        "sample_id",
        "source_line",
        "source_hash",
        "record_type",
        "summary_redacted",
        "has_timestamp",
        "has_source_node",
        "has_privacy_class",
        "has_retention_policy",
        "has_replay_pointer",
        "has_guardian_review",
        "has_lineage",
        "has_governance_state",
        "privacy_confidence",
        "sync_eligibility",
        "replay_coverage_status",
        "requires_human_review",
        "metadata_gap_count",
        "notes",
    }
    for record in data["records"]:
        assert required_fields <= set(record)


def test_audit_uses_allowed_classification_values() -> None:
    run_audit()
    data = load_audit()
    privacy_values = {"high", "medium", "low", "unknown"}
    sync_values = {
        "eligible_governance_only",
        "eligible_summary_only",
        "eligible_evidence_only",
        "not_eligible_sensitive",
        "not_eligible_unresolved_conflict",
        "not_eligible_missing_replay",
        "requires_human_review",
        "unknown",
    }
    replay_values = {"explicit", "derived", "missing", "not_applicable", "unknown"}
    record_types = {
        "governance",
        "telemetry",
        "phase_summary",
        "guardian_observation",
        "system_observation",
        "policy",
        "unknown",
    }
    for record in data["records"]:
        assert record["privacy_confidence"] in privacy_values
        assert record["sync_eligibility"] in sync_values
        assert record["replay_coverage_status"] in replay_values
        assert record["record_type"] in record_types


def test_audit_does_not_expose_known_sensitive_raw_content() -> None:
    run_audit()
    data = load_audit()
    summaries = "\n".join(record["summary_redacted"] for record in data["records"])
    forbidden_fragments = [
        "52-0A40237-H2.local",
        "conversation_id",
        "generation_id",
        "workspace_roots",
        "memory_usage",
        "disk_usage",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in summaries
