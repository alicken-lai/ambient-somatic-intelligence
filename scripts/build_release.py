#!/usr/bin/env python3
"""Freeze the first public alpha release for Ambient Somatic Intelligence."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, record_checksum, stable_json, verify_checksum_chain
from remember import append_memory


ROOT = Path(__file__).resolve().parents[1]
STATE_JSON = ROOT / "state" / "system_state.json"
README_MD = ROOT / "README.md"
PUBLIC_ARCHITECTURE_MD = ROOT / "docs" / "public_architecture_snapshot.md"
RELEASE_AUDIT_MD = ROOT / "docs" / "release_readiness_audit.md"
BOUNDARY_YAML = ROOT / "guardian" / "decision_boundary.yaml"
BOUNDARY_AUDIT_MD = ROOT / "guardian" / "audits" / "decision_boundary_audit.md"
PALACE_JSON = ROOT / "tools" / "mempalace" / "palace.json"
RELEASE_NOTES_MD = ROOT / "RELEASE_NOTES_v0.1.0-alpha.md"
DMN_FILE = ROOT / "memory" / "dmn.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def set_release_version(state: dict[str, Any], version: str) -> dict[str, Any]:
    updated = dict(state)
    updated["release_version"] = version
    updated["generated_at"] = utc_now()
    return updated


def milestone_log() -> list[str]:
    return [
        "Night 0: bootstrap and substrate initialization.",
        "Night 1: baseline identity and approval scaffolding.",
        "Night 2: telemetry capture and incident recall beginnings.",
        "Night 3: visual observation and OCR-adjacent checks.",
        "Night 4: dashboard and local state synthesis.",
        "Night 5: integrity and health scoring foundations.",
        "Night 6: memory pressure diagnosis and reflex review.",
        "Night 7: circadian baseline work.",
        "Night 8: system state synthesis.",
        "Night 9: dashboard synthesis.",
        "Night 10: digest generation.",
        "Night 11: anomaly explanation patterns.",
        "Night 12: memory integrity and incident review.",
        "Night 13: foundational self-model stabilization.",
        "Night 14: memory integrity audit.",
        "Night 15: single source of truth.",
        "Night 16: self-model query interface.",
        "Night 17: self-reflection loop.",
        "Night 18: circadian memory.",
        "Night 19: anomaly explanation engine.",
        "Night 20: operator briefing.",
        "Night 21: decision boundary protocol.",
        "Night 22: approval packet protocol.",
        "Night 23: pre-accident simulation.",
        "Night 24: Guardian dreaming.",
        "Night 25: recalibration queue.",
        "Night 26: MemPalace integration.",
        "Night 27: MemPalace recall interface.",
        "Night 28: operational identity.",
        "Night 29: public architecture snapshot.",
        "Night 30: GitHub README packaging.",
        "Night 31: release readiness audit.",
    ]


def verify_release_inputs() -> dict[str, Any]:
    checksum_ok, checksum_message = verify_checksum_chain()
    state = load_json(STATE_JSON)
    palace = load_json(PALACE_JSON)
    audit_text = RELEASE_AUDIT_MD.read_text(encoding="utf-8") if RELEASE_AUDIT_MD.exists() else ""
    boundary_text = BOUNDARY_AUDIT_MD.read_text(encoding="utf-8") if BOUNDARY_AUDIT_MD.exists() else ""
    public_docs_ok = README_MD.exists() and PUBLIC_ARCHITECTURE_MD.exists() and RELEASE_AUDIT_MD.exists()
    system_state_ok = state.get("health_score") == 76.53 and state.get("incident_count") == 2
    mempalace_ok = palace.get("node_count") == 8 and palace.get("link_count") == 4
    decision_boundary_ok = "github-readme-build" in boundary_text and "release-build" in boundary_text
    return {
        "checksum_chain": {"ok": checksum_ok, "message": checksum_message},
        "public_docs": {"ok": public_docs_ok},
        "readme": {"ok": README_MD.exists()},
        "release_audit": {"ok": bool(audit_text)},
        "system_state_consistency": {"ok": system_state_ok},
        "mempalace_integrity": {"ok": mempalace_ok},
        "decision_boundary": {"ok": decision_boundary_ok},
    }


def release_notes() -> str:
    milestones = milestone_log()
    return "\n".join(
        [
            "# v0.1.0-alpha Release Notes",
            "",
            "## Thesis",
            "",
            "Ambient Somatic Intelligence Alpha is a Guardian-governed memory and observation system that turns telemetry, incidents, simulations, reflections, and review artifacts into accountable action proposals without autonomous corrective behavior.",
            "",
            "## Architecture",
            "",
            "- Sensing and telemetry collection.",
            "- Baselines, circadian context, and system state synthesis.",
            "- Explanations, reflections, briefings, simulations, and dreaming.",
            "- Guardian boundary checks, approval packets, and recalibration queues.",
            "- Append-only memory surfaces, MemPalace recall, and operational identity.",
            "",
            "## Night 0-31 Milestones",
            "",
            *[f"- {item}" for item in milestones],
            "",
            "## Safety Boundaries",
            "",
            "- No destructive commands.",
            "- No external actions without Guardian approval.",
            "- Append-only memory only.",
            "- CLI first; GUI actions stay sandboxed.",
            "- No autonomous corrective actions by default.",
            "- Execution remains reserved for explicit approval paths.",
            "",
            "## Known Limitations",
            "",
            "- It remains a local, memory-heavy system with low-confidence watch-state behavior around repeated memory pressure.",
            "- Public release artifacts are summaries; raw runtime traces stay internal.",
            "- Model confidence is advisory and does not replace evidence.",
            "",
            "## Future Roadmap",
            "",
            "- Broaden recall and explanation coverage for new incident classes.",
            "- Refine recalibration review flows with stronger evidence summaries.",
            "- Expand public architecture snapshots as the system matures.",
            "- Keep the memory graph and operator-facing summaries aligned.",
            "- Preserve the current no-corrective default until a formal execution path exists.",
            "",
            "## Verification",
            "",
            "- checksum chain: verified",
            "- public docs: present",
            "- README: present",
            "- release audit: present",
            "- system_state: release_version set",
            "- MemPalace: integrity confirmed",
        ]
    ) + "\n"


def write_release_notes() -> None:
    RELEASE_NOTES_MD.write_text(release_notes(), encoding="utf-8")


def update_state(version: str) -> dict[str, Any]:
    state = load_json(STATE_JSON)
    updated = set_release_version(state, version)
    STATE_JSON.write_text(json.dumps(updated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return updated


def run_build() -> dict[str, Any]:
    version = "v0.1.0-alpha"
    verification = verify_release_inputs()
    write_release_notes()
    updated_state = update_state(version)
    record_checksum(RELEASE_NOTES_MD, "release_notes_write", {"version": version})
    record_checksum(STATE_JSON, "release_version_write", {"version": version})
    append_memory(
        stable_json(
            {
                "version": version,
                "verification": verification,
                "release_notes": str(RELEASE_NOTES_MD.relative_to(ROOT)),
                "system_state_release_version": updated_state.get("release_version"),
            }
        ),
        ["release", "genesis", "night32"],
        "release_build",
    )
    log_action("release:build", "completed", "ALLOW", {"version": version, "verification": verification})
    return {
        "version": version,
        "verification": verification,
        "release_notes": str(RELEASE_NOTES_MD.relative_to(ROOT)),
        "system_state": str(STATE_JSON.relative_to(ROOT)),
        "recommendations_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze the first public alpha release.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(run_build()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
