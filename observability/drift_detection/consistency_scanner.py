"""
Consistency Scanner — Scans architecture for structural inconsistencies.

Detects orphaned modules, missing __init__.py exports, broken import references,
unregistered subsystems, and unregistered agents by comparing the filesystem
state against the self-model's topology.
"""

from __future__ import annotations

import ast
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from identity.cognitive_self_model.self_model import CognitiveSelfModel

logger = logging.getLogger("observability.drift_detection.consistency_scanner")

AMBIENT_ROOT = Path(__file__).resolve().parent.parent.parent

KNOWN_SUBSYSTEMS = [
    "kernel", "agents", "governance", "memory", "context",
    "runtime/task_graph", "somatic", "observability",
]


class IssueSeverity(str, Enum):
    """Severity levels for detected inconsistencies."""
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ConsistencyIssue:
    """A single detected inconsistency."""
    category: str
    description: str
    severity: IssueSeverity
    location: str = ""
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "description": self.description,
            "severity": self.severity.value,
            "location": self.location,
            "suggestion": self.suggestion,
        }


@dataclass
class ConsistencyScanResult:
    """Result of a full consistency scan."""
    issues: list[ConsistencyIssue] = field(default_factory=list)
    overall_score: float = 100.0
    scan_timestamp: str = ""
    elapsed_ms: float = 0.0
    modules_scanned: int = 0
    subsystems_scanned: int = 0

    def to_dict(self) -> dict[str, Any]:
        severity_counts = {}
        for issue in self.issues:
            sev = issue.severity.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        return {
            "issues": [i.to_dict() for i in self.issues],
            "issue_count": len(self.issues),
            "severity_counts": severity_counts,
            "overall_score": round(self.overall_score, 1),
            "scan_timestamp": self.scan_timestamp,
            "elapsed_ms": round(self.elapsed_ms, 1),
            "modules_scanned": self.modules_scanned,
            "subsystems_scanned": self.subsystems_scanned,
        }


class ConsistencyScanner:
    """
    Scans architecture for inconsistencies.

    Takes a CognitiveSelfModel and performs multiple checks:
      1. Orphaned modules (exist on disk but not imported)
      2. Missing __init__.py exports
      3. Broken import references
      4. Subsystems not registered in kernel
      5. Agents not registered in registry
    """

    def __init__(self, root: Path | None = None):
        self._root = root or AMBIENT_ROOT

    def scan(self, self_model: "CognitiveSelfModel") -> ConsistencyScanResult:
        """Run all consistency checks against the self-model."""
        from datetime import datetime, timezone

        logger.info("Starting consistency scan...")
        start = time.monotonic()

        issues: list[ConsistencyIssue] = []
        modules_scanned = 0
        subsystems_scanned = 0

        topology = self_model.get_system_topology()
        subsystems = topology.get("subsystems", {})
        subsystems_scanned = len(subsystems)

        for sub_name, sub_data in subsystems.items():
            modules_scanned += len(sub_data.get("modules", []))

        orphaned = self._detect_orphaned_modules(subsystems)
        issues.extend(orphaned)

        missing_exports = self._detect_missing_exports(subsystems)
        issues.extend(missing_exports)

        broken_imports = self._detect_broken_imports(subsystems)
        issues.extend(broken_imports)

        unregistered_subs = self._detect_unregistered_subsystems()
        issues.extend(unregistered_subs)

        unregistered_agents = self._detect_unregistered_agents(subsystems)
        issues.extend(unregistered_agents)

        elapsed = (time.monotonic() - start) * 1000
        score = self._compute_score(issues)

        result = ConsistencyScanResult(
            issues=issues,
            overall_score=score,
            scan_timestamp=datetime.now(timezone.utc).isoformat(),
            elapsed_ms=elapsed,
            modules_scanned=modules_scanned,
            subsystems_scanned=subsystems_scanned,
        )

        logger.info(
            "Consistency scan complete: %d issues, score=%.1f (%.1fms)",
            len(issues), score, elapsed,
        )
        return result

    # ── Detection Methods ────────────────────────────────────────────────

    def _detect_orphaned_modules(self, subsystems: dict[str, Any]) -> list[ConsistencyIssue]:
        """Find .py files that exist but aren't imported by anything."""
        issues: list[ConsistencyIssue] = []

        all_imports: set[str] = set()
        all_module_paths: set[str] = set()

        for sub_data in subsystems.values():
            for mod in sub_data.get("modules", []):
                mod_path = mod.get("path", "")
                all_module_paths.add(mod_path)
                for imp in mod.get("imports", []):
                    all_imports.add(imp)

        for sub_path_str in KNOWN_SUBSYSTEMS:
            sub_dir = self._root / sub_path_str
            if not sub_dir.is_dir():
                continue

            for py_file in sub_dir.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue

                rel_path = str(py_file.relative_to(self._root))

                module_import_name = (
                    rel_path.replace("/", ".").replace(".py", "")
                )

                is_imported = any(
                    module_import_name == imp or module_import_name.endswith("." + imp)
                    or imp.startswith(module_import_name)
                    for imp in all_imports
                )

                is_in_topology = rel_path in all_module_paths

                if not is_imported and not is_in_topology:
                    parent_init = py_file.parent / "__init__.py"
                    if parent_init.exists():
                        init_content = parent_init.read_text(encoding="utf-8")
                        stem = py_file.stem
                        if stem in init_content:
                            continue

                    issues.append(ConsistencyIssue(
                        category="orphaned_module",
                        description=f"Module '{py_file.stem}' exists but may not be imported",
                        severity=IssueSeverity.LOW,
                        location=rel_path,
                        suggestion="Verify module is used or consider removing it",
                    ))

        return issues

    def _detect_missing_exports(self, subsystems: dict[str, Any]) -> list[ConsistencyIssue]:
        """Find modules with public classes not exported in __init__.py."""
        issues: list[ConsistencyIssue] = []

        for sub_path_str in KNOWN_SUBSYSTEMS:
            sub_dir = self._root / sub_path_str
            init_file = sub_dir / "__init__.py"

            if not init_file.exists():
                issues.append(ConsistencyIssue(
                    category="missing_init",
                    description=f"Subsystem '{sub_path_str}' has no __init__.py",
                    severity=IssueSeverity.MEDIUM,
                    location=str(sub_dir.relative_to(self._root)),
                    suggestion="Add __init__.py with proper exports",
                ))
                continue

            try:
                init_content = init_file.read_text(encoding="utf-8")
            except OSError:
                continue

            sub_name = sub_path_str.replace("/", ".")
            sub_data = subsystems.get(sub_name, {})

            for mod in sub_data.get("modules", []):
                if mod.get("name", "") == "__init__":
                    continue
                for cls in mod.get("classes", []):
                    cls_name = cls.get("name", "")
                    if cls_name.startswith("_"):
                        continue
                    if cls_name not in init_content:
                        issues.append(ConsistencyIssue(
                            category="missing_export",
                            description=(
                                f"Class '{cls_name}' in {mod.get('path', '')} "
                                f"not exported from {sub_path_str}/__init__.py"
                            ),
                            severity=IssueSeverity.INFO,
                            location=mod.get("path", ""),
                            suggestion=f"Add '{cls_name}' to __all__ in __init__.py",
                        ))

        return issues

    def _detect_broken_imports(self, subsystems: dict[str, Any]) -> list[ConsistencyIssue]:
        """Find imports that reference non-existent modules."""
        issues: list[ConsistencyIssue] = []

        known_modules: set[str] = set()
        for sub_name, sub_data in subsystems.items():
            known_modules.add(sub_name)
            for mod in sub_data.get("modules", []):
                mod_path = mod.get("path", "")
                import_name = mod_path.replace("/", ".").replace(".py", "")
                known_modules.add(import_name)
                known_modules.add(mod.get("name", ""))

        for sub_name, sub_data in subsystems.items():
            for mod in sub_data.get("modules", []):
                for imp in mod.get("imports", []):
                    if self._is_stdlib_or_external(imp):
                        continue

                    imp_parts = imp.split(".")
                    top_level = imp_parts[0]
                    if top_level in ("kernel", "agents", "governance", "memory",
                                     "context", "runtime", "somatic", "observability",
                                     "identity", "scripts", "tools"):
                        resolved_path = self._root / imp.replace(".", "/")
                        if not (resolved_path.exists()
                                or resolved_path.with_suffix(".py").exists()
                                or (resolved_path / "__init__.py").exists()):
                            issues.append(ConsistencyIssue(
                                category="broken_import",
                                description=(
                                    f"Import '{imp}' in {mod.get('path', '')} "
                                    f"cannot be resolved on disk"
                                ),
                                severity=IssueSeverity.HIGH,
                                location=mod.get("path", ""),
                                suggestion="Fix import path or create the missing module",
                            ))

        return issues

    def _detect_unregistered_subsystems(self) -> list[ConsistencyIssue]:
        """Check if subsystem directories exist but aren't in kernel __init__.py."""
        issues: list[ConsistencyIssue] = []

        kernel_init = self._root / "kernel" / "__init__.py"
        if not kernel_init.exists():
            return issues

        try:
            kernel_content = kernel_init.read_text(encoding="utf-8")
        except OSError:
            return issues

        for sub_path in KNOWN_SUBSYSTEMS:
            sub_dir = self._root / sub_path
            if not sub_dir.is_dir():
                continue

            sub_name = sub_path.split("/")[0]
            if sub_name == "kernel":
                continue

            if sub_name not in kernel_content:
                issues.append(ConsistencyIssue(
                    category="unregistered_subsystem",
                    description=f"Subsystem '{sub_name}' not referenced in kernel/__init__.py",
                    severity=IssueSeverity.MEDIUM,
                    location=sub_path,
                    suggestion="Register subsystem in AmbientKernel",
                ))

        return issues

    def _detect_unregistered_agents(self, subsystems: dict[str, Any]) -> list[ConsistencyIssue]:
        """Check if agent classes exist but may not be in the registry."""
        issues: list[ConsistencyIssue] = []

        agents_data = subsystems.get("agents", {})
        agent_classes: list[str] = []

        for mod in agents_data.get("modules", []):
            for cls in mod.get("classes", []):
                cls_name = cls.get("name", "")
                bases = cls.get("base_classes", [])
                if ("BaseAgent" in bases or cls_name.endswith("Agent")) and cls_name != "BaseAgent":
                    agent_classes.append(cls_name)

        registry_file = self._root / "agents" / "registry.py"
        if registry_file.exists():
            try:
                registry_content = registry_file.read_text(encoding="utf-8")
                for agent_cls in agent_classes:
                    if agent_cls not in registry_content:
                        issues.append(ConsistencyIssue(
                            category="unregistered_agent",
                            description=f"Agent class '{agent_cls}' not found in registry.py",
                            severity=IssueSeverity.LOW,
                            location="agents/registry.py",
                            suggestion=f"Register '{agent_cls}' in AgentRegistry",
                        ))
            except OSError:
                pass

        return issues

    # ── Internal Helpers ─────────────────────────────────────────────────

    def _compute_score(self, issues: list[ConsistencyIssue]) -> float:
        """Compute overall consistency score (0-100)."""
        if not issues:
            return 100.0

        penalty_map = {
            IssueSeverity.INFO: 1,
            IssueSeverity.LOW: 3,
            IssueSeverity.MEDIUM: 7,
            IssueSeverity.HIGH: 15,
            IssueSeverity.CRITICAL: 30,
        }

        total_penalty = sum(penalty_map.get(i.severity, 5) for i in issues)
        return max(0.0, 100.0 - total_penalty)

    @staticmethod
    def _is_stdlib_or_external(import_path: str) -> bool:
        """Check if an import is standard library or known external."""
        stdlib_prefixes = {
            "os", "sys", "json", "re", "math", "time", "datetime", "pathlib",
            "typing", "dataclasses", "enum", "collections", "hashlib", "logging",
            "importlib", "inspect", "ast", "abc", "functools", "itertools",
            "copy", "io", "uuid", "traceback", "threading", "queue", "textwrap",
            "__future__",
        }
        top = import_path.split(".")[0]
        return top in stdlib_prefixes
