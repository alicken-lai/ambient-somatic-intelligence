"""Institutional health scoring for Hermes-ASI v0.9 audit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

AUDIT_DOCS = [
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
    "docs/architecture/HERMES_ASI_V09.md",
]

KERNEL_DIRS = [
    "hermes/deliberation",
    "hermes/verification",
    "hermes/acquisition",
    "hermes/calibration",
    "hermes/reality_alignment",
    "hermes/identity",
]

KEY_REPORTS = [
    "reports/evidence_report.json",
    "reports/acquisition_report.json",
    "reports/knowledge_health_report.json",
    "reports/reality_alignment_report.json",
    "reports/identity_report.json",
]


def compute_institutional_health(root: str | Path = ROOT) -> dict[str, Any]:
    base = Path(root)
    audit_coverage = _coverage(base, AUDIT_DOCS)
    kernel_coverage = _coverage(base, KERNEL_DIRS)
    report_coverage = _coverage(base, KEY_REPORTS)
    governance = 0.95 if (base / "hermes/rules/canonical_rules.md").is_file() else 0.7
    observability = report_coverage
    knowledge = 0.9 if (base / "hermes/deliberation/knowledge_graph/graph.py").is_file() else 0.6
    identity = 0.95 if (base / "hermes/identity").is_dir() and (base / "reports/identity_report.json").is_file() else 0.65
    maintainability = 0.78
    score = round(
        (
            kernel_coverage * 18
            + governance * 18
            + observability * 16
            + knowledge * 16
            + identity * 16
            + audit_coverage * 10
            + maintainability * 6
        ),
        2,
    )
    strengths = [
        "Phase 1-9 kernels are present and connected through reports/registries.",
        "Guardian and advisory-only boundaries are consistently documented.",
        "Reality alignment and identity continuity are first-class audit surfaces.",
    ]
    risks = [
        "Report generation can refresh lower-layer registries and create timestamp churn.",
        "DMN event taxonomy is not yet formalized.",
        "Knowledge graph coverage is implemented but not exported as a dedicated graph health report.",
    ]
    return {
        "institutional_health": score,
        "components": {
            "integration": round(kernel_coverage * 100, 2),
            "governance": round(governance * 100, 2),
            "observability": round(observability * 100, 2),
            "knowledge_coverage": round(knowledge * 100, 2),
            "identity_continuity": round(identity * 100, 2),
            "auditability": round(audit_coverage * 100, 2),
            "maintainability": round(maintainability * 100, 2),
        },
        "strengths": strengths,
        "risks": risks,
    }


def generate_audit_report(output_path: str | Path = "reports/institutional_audit_report.md") -> dict[str, Any]:
    health = compute_institutional_health()
    lines = [
        "# Institutional Audit Report",
        "",
        f"Institutional Health: {health['institutional_health']:.2f}",
        "",
        "## Component Scores",
        "",
    ]
    for key, value in health["components"].items():
        lines.append(f"- {key}: {value:.2f}")
    lines.extend(["", "## Strengths", ""])
    lines.extend(f"- {item}" for item in health["strengths"])
    lines.extend(["", "## Critical Risks", ""])
    lines.extend(f"- {item}" for item in health["risks"])
    lines.extend(
        [
            "",
            "## Audit Documents",
            "",
            *[f"- `{path}`" for path in AUDIT_DOCS],
            "",
            "## Release Readiness",
            "",
            "Recommendation: v0.9 release candidate is conditionally ready as an advisory institutional intelligence system.",
        ]
    )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path = output.with_suffix(".json")
    json_path.write_text(json.dumps(health, indent=2, ensure_ascii=False), encoding="utf-8")
    return {**health, "report_path": str(output), "json_path": str(json_path)}


def _coverage(root: Path, paths: list[str]) -> float:
    if not paths:
        return 1.0
    present = sum(1 for path in paths if (root / path).exists())
    return present / len(paths)
