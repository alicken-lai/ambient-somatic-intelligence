"""v0.4.4B governed coverage — high-risk, overall, and trace metrics."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from kernel.isolation.write_target import WriteTarget
from observability.v04.authority_trace import AuthorityTrace
from observability.v04.migration_coverage import (
    DEFAULT_INVENTORY,
    GUARD_MARKERS,
    MIGRATED_MODULES,
    _file_has_guard,
    _load_inventory,
    _path_migrated,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

HIGH_RISK_TARGETS = frozenset({
    WriteTarget.MEMORY.value,
    WriteTarget.GOVERNANCE_AUDIT.value,
    WriteTarget.TRUTH_GRAPH.value,
    WriteTarget.SKILL_REGISTRY.value,
    WriteTarget.STATE.value,
    WriteTarget.TELEMETRY.value,
    WriteTarget.RELEASE_DOCS.value,
    "memory/dmn.jsonl",
    "governance_audit",
    "state/checkpoint",
})

HIGH_RISK_MODULES = frozenset({
    "governance/audit_log.py",
    "memory/memory_kernel.py",
    "kernel/isolation/governed_memory_writer.py",
    "skills/core/skill_registry.py",
    "kernel/truth/truth_registry.py",
    "kernel/wiring/patch_registry.py",
    "architecture/bus_decomposition/event_schema.py",
    "kernel/integration_bus.py",
    "somatic/signal_bus.py",
})

TRACE_MARKERS = re.compile(
    r"record_guarded_operation|authority_trace|GovernedMemoryWriter|RegistryGuard",
    re.I,
)

GOVERNED_CALL_MARKERS = re.compile(
    r"audit_log\.record_|GovernanceAuditLog|GuardedFileWriter|GovernedMemoryWriter|"
    r"register_guarded_callback|registry_guard\.mutate|execution_context|skill_registry\.",
    re.I,
)

HIGH_RISK_COVERAGE_TARGET = 1.0
OVERALL_COVERAGE_TARGET = 0.35
TRACE_COVERAGE_TARGET = 0.70


@dataclass
class GovernedCoverageReport:
    high_risk_total: int = 0
    high_risk_migrated: int = 0
    high_risk_coverage: float = 0.0
    overall_total: int = 0
    overall_migrated: int = 0
    overall_coverage: float = 0.0
    trace_coverage: float = 0.0
    high_risk_gate_pass: bool = False
    overall_gate_pass: bool = False
    trace_gate_pass: bool = False
    migrated_modules: list[str] = field(default_factory=list)
    honesty_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "high_risk_total": self.high_risk_total,
            "high_risk_migrated": self.high_risk_migrated,
            "high_risk_coverage": round(self.high_risk_coverage, 4),
            "overall_total": self.overall_total,
            "overall_migrated": self.overall_migrated,
            "overall_coverage": round(self.overall_coverage, 4),
            "trace_coverage": round(self.trace_coverage, 4),
            "high_risk_gate_pass": self.high_risk_gate_pass,
            "overall_gate_pass": self.overall_gate_pass,
            "trace_gate_pass": self.trace_gate_pass,
            "targets": {
                "high_risk": HIGH_RISK_COVERAGE_TARGET,
                "overall": OVERALL_COVERAGE_TARGET,
                "trace": TRACE_COVERAGE_TARGET,
            },
            "migrated_modules": self.migrated_modules,
            "honesty_note": self.honesty_note,
        }


OUT_OF_SCOPE_PREFIXES = frozenset({
    "memory/ontology/",
    "ontology/",
    "guardian/",
    "telemetry/maturation/",
})


def _is_high_risk_entry(entry: dict) -> bool:
    path = entry.get("path", "")
    rel = path.split(":")[0] if ":" in path else path
    if any(rel.startswith(p) for p in OUT_OF_SCOPE_PREFIXES):
        return False
    if entry.get("risk_level") == "high":
        return True
    wt = str(entry.get("write_target", ""))
    if wt in HIGH_RISK_TARGETS:
        return True
    return rel in HIGH_RISK_MODULES


def _entry_governed(entry: dict, repo_root: Path) -> bool:
    if _path_migrated(entry, repo_root):
        return True
    path_str = entry.get("path", "")
    if ":" not in path_str:
        return False
    rel, _line = path_str.split(":", 1)
    file_path = repo_root / rel
    if not file_path.is_file():
        return False
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return bool(GOVERNED_CALL_MARKERS.search(text))


def _module_trace_ready(module_path: str) -> bool:
    fp = REPO_ROOT / module_path
    if not fp.is_file():
        return False
    try:
        text = fp.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return bool(TRACE_MARKERS.search(text))


def compute_governed_coverage(
    inventory_path: Path | None = None,
    *,
    repo_root: Path | None = None,
    trace: AuthorityTrace | None = None,
) -> GovernedCoverageReport:
    root = repo_root or REPO_ROOT
    inventory = _load_inventory(inventory_path or DEFAULT_INVENTORY)
    entries = inventory.get("entries", [])

    high_risk_entries = [e for e in entries if _is_high_risk_entry(e)]
    hr_migrated = sum(1 for e in high_risk_entries if _entry_governed(e, root))
    hr_total = len(high_risk_entries)
    hr_cov = hr_migrated / hr_total if hr_total else 1.0

    overall_migrated = sum(1 for e in entries if _entry_governed(e, root))
    overall_total = len(entries)
    overall_cov = overall_migrated / overall_total if overall_total else 0.0

    module_trace_hits = sum(1 for m in HIGH_RISK_MODULES if _module_trace_ready(m))
    trace_module_ratio = module_trace_hits / len(HIGH_RISK_MODULES)

    trace_event_ratio = 0.0
    if trace is not None:
        events = trace.recent(limit=500)
        if events:
            guarded = sum(1 for e in events if e.get("mutation_type"))
            trace_event_ratio = guarded / len(events)

    trace_cov = max(trace_module_ratio, trace_event_ratio)

    migrated_modules = sorted(
        m for m in HIGH_RISK_MODULES if (root / m).is_file() and _module_trace_ready(m)
    )

    note = ""
    scanned = int(inventory.get("total_scanned_mutations", overall_total))
    if scanned > overall_total:
        note = (
            f"Overall coverage uses {overall_total} catalogued paths; "
            f"v043 metadata reports {scanned} scanned."
        )

    return GovernedCoverageReport(
        high_risk_total=hr_total,
        high_risk_migrated=hr_migrated,
        high_risk_coverage=hr_cov,
        overall_total=overall_total,
        overall_migrated=overall_migrated,
        overall_coverage=overall_cov,
        trace_coverage=trace_cov,
        high_risk_gate_pass=hr_cov >= HIGH_RISK_COVERAGE_TARGET,
        overall_gate_pass=overall_cov >= OVERALL_COVERAGE_TARGET,
        trace_gate_pass=trace_cov >= TRACE_COVERAGE_TARGET,
        migrated_modules=migrated_modules,
        honesty_note=note,
    )
