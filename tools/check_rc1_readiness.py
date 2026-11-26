#!/usr/bin/env python3
"""Hermes-ASI v0.9.0-rc1 release readiness checker.

Verifies all required release artifacts exist, audit documents are present,
and health thresholds pass. Read-only: emits only to stdout. Zero third-party
dependencies (stdlib only). Cross-platform (uses pathlib, no hardcoded
separators).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_RELEASE_DOCS: list[tuple[str, str]] = [
    ("RELEASE_NOTES_v0.9.0-rc1.md", "Release notes"),
    ("docs/release/CAPABILITY_MATRIX.md", "Capability matrix"),
    ("docs/release/CLI_REFERENCE.md", "CLI reference"),
    ("docs/release/REPORT_REFERENCE.md", "Report reference"),
    ("docs/release/TEST_SUMMARY.md", "Test summary"),
    ("docs/release/ARCHITECTURE_SNAPSHOT.md", "Architecture snapshot"),
    ("docs/release/GOVERNANCE_LOCK.md", "Governance lock"),
    ("docs/release/KNOWN_LIMITATIONS.md", "Known limitations"),
    ("RELEASE_MANIFEST_v0.9.0-rc1.md", "Release manifest"),
    ("reports/v090_rc1_baseline.json", "RC1 baseline metrics"),
    ("reports/v090_rc1_release_report.md", "RC1 release report"),
    ("docs/release/RELEASE_DECISION.md", "Release decision"),
]


REQUIRED_AUDIT_DOCS: list[str] = [
    "docs/audit/KERNEL_DEPENDENCY_AUDIT.md",
    "docs/audit/LIFECYCLE_AUDIT.md",
    "docs/audit/GOVERNANCE_AUDIT.md",
    "docs/audit/DMN_AUDIT.md",
    "docs/audit/KNOWLEDGE_GRAPH_AUDIT.md",
    "docs/audit/OBSERVABILITY_AUDIT.md",
    "docs/audit/REPORT_INVENTORY.md",
    "docs/audit/RUNTIME_STATE_AUDIT.md",
    "docs/audit/GIT_HYGIENE_AUDIT.md",
    "docs/audit/README_AUDIT.md",
    "docs/audit/TECHNICAL_DEBT.md",
    "docs/audit/RELEASE_REVIEW.md",
]


REQUIRED_EXISTING_BASE: list[str] = [
    "VERSION_MANIFEST.md",
    "docs/architecture/HERMES_ASI_V09.md",
    "docs/release/V09_RELEASE_CHECKLIST.md",
    "guardian/policy.yaml",
    "hermes/rules/canonical_rules.md",
]


HEALTH_REPORT_PATHS: list[str] = [
    "reports/v09_release_report.json",
    "reports/institutional_audit_report.json",
    "reports/graph_health_report.json",
]


THRESHOLDS: dict[str, float] = {
    "rc_health_min": 85.0,
    "dmn_health_min": 80.0,
    "graph_health_min": 75.0,
}


def _missing_message(description: str, relative_path: str) -> str:
    return f"Missing: {description} at {relative_path}"


def check_artifacts_exist(base: Path) -> list[str]:
    missing: list[str] = []
    for relative_path, description in REQUIRED_RELEASE_DOCS:
        if not (base / relative_path).is_file():
            missing.append(_missing_message(description, relative_path))
    return missing


def check_audit_docs_exist(base: Path) -> list[str]:
    missing: list[str] = []
    for relative_path in REQUIRED_AUDIT_DOCS:
        if not (base / relative_path).is_file():
            missing.append(_missing_message(relative_path, relative_path))
    return missing


def check_existing_base(base: Path) -> list[str]:
    missing: list[str] = []
    for relative_path in REQUIRED_EXISTING_BASE:
        if not (base / relative_path).is_file():
            missing.append(_missing_message(relative_path, relative_path))
    return missing


def load_json(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"warning: cannot read {path}: {exc}", file=sys.stderr)
        return {}
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"warning: invalid JSON in {path}: {exc}", file=sys.stderr)
        return {}
    if not isinstance(loaded, dict):
        print(f"warning: top-level JSON in {path} is not an object", file=sys.stderr)
        return {}
    return loaded


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def check_health_thresholds(base: Path) -> tuple[dict[str, float | None], list[str]]:
    scores: dict[str, float | None] = {
        "rc_health": None,
        "dmn_health": None,
        "graph_health": None,
    }
    failures: list[str] = []

    report_path = base / "reports" / "v09_release_report.json"
    if not report_path.is_file():
        failures.append(f"Missing: RC release report at reports/v09_release_report.json")
        return scores, failures

    data = load_json(report_path)
    if not data:
        failures.append(
            "Unreadable: reports/v09_release_report.json (missing or malformed JSON)"
        )
        return scores, failures

    rc_raw = data.get("rc_health")
    rc_value = _coerce_float(rc_raw)
    scores["rc_health"] = rc_value
    if rc_value is None:
        failures.append(
            f"Threshold rc_health: missing or non-numeric value ({rc_raw!r}); min {THRESHOLDS['rc_health_min']}"
        )
    elif rc_value < THRESHOLDS["rc_health_min"]:
        failures.append(
            f"Threshold rc_health: {rc_value} below minimum {THRESHOLDS['rc_health_min']}"
        )

    components = data.get("components")
    component_dmn = None
    component_graph = None
    if isinstance(components, dict):
        component_dmn = components.get("dmn_health")
        component_graph = components.get("graph_health")

    dmn_value = _coerce_float(component_dmn)
    scores["dmn_health"] = dmn_value
    if dmn_value is None:
        failures.append(
            f"Threshold dmn_health: missing or non-numeric value ({component_dmn!r}); min {THRESHOLDS['dmn_health_min']}"
        )
    elif dmn_value < THRESHOLDS["dmn_health_min"]:
        failures.append(
            f"Threshold dmn_health: {dmn_value} below minimum {THRESHOLDS['dmn_health_min']}"
        )

    graph_value = _coerce_float(component_graph)
    scores["graph_health"] = graph_value
    if graph_value is None:
        failures.append(
            f"Threshold graph_health: missing or non-numeric value ({component_graph!r}); min {THRESHOLDS['graph_health_min']}"
        )
    elif graph_value < THRESHOLDS["graph_health_min"]:
        failures.append(
            f"Threshold graph_health: {graph_value} below minimum {THRESHOLDS['graph_health_min']}"
        )

    return scores, failures


def check_release_ready_flag(base: Path) -> list[str]:
    failures: list[str] = []
    report_path = base / "reports" / "v09_release_report.json"
    if not report_path.is_file():
        failures.append("Missing: reports/v09_release_report.json (cannot read release_ready flag)")
        return failures

    data = load_json(report_path)
    if not data:
        failures.append(
            "Unreadable: reports/v09_release_report.json (cannot read release_ready flag)"
        )
        return failures

    if data.get("release_ready") is not True:
        failures.append(
            f"release_ready flag is not true (got {data.get('release_ready')!r})"
        )
    return failures


def run_all_checks(base: Path) -> dict[str, Any]:
    artifacts_missing = check_artifacts_exist(base)
    audit_missing = check_audit_docs_exist(base)
    base_missing = check_existing_base(base)
    scores, health_failures = check_health_thresholds(base)
    flag_failures = check_release_ready_flag(base)

    checks: dict[str, Any] = {
        "release_artifacts": {
            "passed": not artifacts_missing,
            "missing": artifacts_missing,
        },
        "audit_docs": {
            "passed": not audit_missing,
            "missing": audit_missing,
        },
        "existing_base": {
            "passed": not base_missing,
            "missing": base_missing,
        },
        "health_thresholds": {
            "passed": not health_failures,
            "scores": scores,
            "failures": health_failures,
        },
        "release_ready_flag": {
            "passed": not flag_failures,
        },
    }

    reasons: list[str] = []
    reasons.extend(artifacts_missing)
    reasons.extend(audit_missing)
    reasons.extend(base_missing)
    reasons.extend(health_failures)
    reasons.extend(flag_failures)

    ready = all(check["passed"] for check in checks.values())
    return {"ready": ready, "reason": reasons, "checks": checks}


def _format_human(base: Path, result: dict[str, Any]) -> str:
    lines: list[str] = [
        "Hermes-ASI v0.9.0-rc1 Readiness Check",
        "======================================",
        f"Base: {base}",
        "",
    ]

    checks = result["checks"]

    artifact_count = len(REQUIRED_RELEASE_DOCS)
    audit_count = len(REQUIRED_AUDIT_DOCS)
    base_count = len(REQUIRED_EXISTING_BASE)

    artifact_missing = checks["release_artifacts"]["missing"]
    audit_missing = checks["audit_docs"]["missing"]
    base_missing = checks["existing_base"]["missing"]
    health = checks["health_thresholds"]
    flag = checks["release_ready_flag"]

    label_width = 44

    lines.append(
        f"[1/5] Release artifacts ({artifact_count} expected)".ljust(label_width)
        + f"... {'PASS' if not artifact_missing else 'FAIL (' + str(len(artifact_missing)) + ' missing)'}"
    )
    for entry in artifact_missing:
        lines.append(f"      - {entry}")

    lines.append(
        f"[2/5] Audit documents ({audit_count} expected)".ljust(label_width)
        + f"... {'PASS' if not audit_missing else 'FAIL (' + str(len(audit_missing)) + ' missing)'}"
    )
    for entry in audit_missing:
        lines.append(f"      - {entry}")

    lines.append(
        f"[3/5] Existing base files ({base_count} expected)".ljust(label_width)
        + f"... {'PASS' if not base_missing else 'FAIL (' + str(len(base_missing)) + ' missing)'}"
    )
    for entry in base_missing:
        lines.append(f"      - {entry}")

    lines.append(
        "[4/5] Health thresholds".ljust(label_width)
        + f"... {'PASS' if health['passed'] else 'FAIL (' + str(len(health['failures'])) + ' failures)'}"
    )
    rc = health["scores"].get("rc_health")
    dmn = health["scores"].get("dmn_health")
    graph = health["scores"].get("graph_health")
    if rc is not None:
        lines.append(
            f"      RC Health:     {rc:>6.2f} (min {THRESHOLDS['rc_health_min']})"
        )
    if dmn is not None:
        lines.append(
            f"      DMN Health:    {dmn:>6.2f} (min {THRESHOLDS['dmn_health_min']})"
        )
    if graph is not None:
        lines.append(
            f"      Graph Health:  {graph:>6.2f} (min {THRESHOLDS['graph_health_min']})"
        )
    for entry in health["failures"]:
        lines.append(f"      - {entry}")

    if flag["passed"]:
        lines.append(
            "[5/5] Release ready flag".ljust(label_width)
            + "... PASS (release_ready=true)"
        )
    else:
        lines.append(
            "[5/5] Release ready flag".ljust(label_width) + "... FAIL"
        )

    lines.append("")
    if result["ready"]:
        lines.append("READY: true")
    else:
        lines.append(f"READY: false ({len(result['reason'])} reasons)")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Hermes-ASI v0.9.0-rc1 release readiness checker"
    )
    parser.add_argument(
        "--base",
        type=Path,
        default=ROOT,
        help=f"Project base directory (default: {ROOT})",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Emit machine-readable JSON instead of human-readable text",
    )
    args = parser.parse_args(argv)

    base: Path = args.base.resolve()
    result = run_all_checks(base)

    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=False))
    else:
        print(_format_human(base, result))

    return 0 if result["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
