"""
Architecture Graph — Queryable model of the Ambient OS system structure.

Builds a graph representation of the codebase by introspecting actual Python
modules, extracting classes, methods, and import dependencies. Works both
with a live kernel instance and in standalone filesystem-scan mode.

Output: SubsystemNode → ModuleNode → ClassNode hierarchy with dependency edges.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import AmbientKernel

logger = logging.getLogger("identity.cognitive_self_model.architecture_graph")

AMBIENT_ROOT = Path(__file__).resolve().parent.parent.parent

KNOWN_SUBSYSTEMS = [
    "kernel",
    "agents",
    "governance",
    "memory",
    "context",
    "runtime/task_graph",
    "somatic",
    "observability",
]


@dataclass
class ClassNode:
    """Represents a single class within a module."""
    name: str
    methods: list[str] = field(default_factory=list)
    base_classes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "methods": self.methods,
            "base_classes": self.base_classes,
        }


@dataclass
class ModuleNode:
    """Represents a single Python module (file)."""
    name: str
    path: str
    classes: list[ClassNode] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "classes": [c.to_dict() for c in self.classes],
            "imports": self.imports,
        }


@dataclass
class SubsystemNode:
    """Represents a top-level subsystem (directory)."""
    name: str
    modules: list[ModuleNode] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    status: str = "active"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "modules": [m.to_dict() for m in self.modules],
            "dependencies": self.dependencies,
            "status": self.status,
        }


@dataclass
class TopologySnapshot:
    """A point-in-time capture of the system architecture."""
    timestamp: str
    subsystems: list[SubsystemNode] = field(default_factory=list)
    edges: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "subsystems": [s.to_dict() for s in self.subsystems],
            "edges": self.edges,
            "metadata": self.metadata,
        }


class ArchitectureGraph:
    """
    Builds and queries a model of the system's architecture by introspecting
    the actual codebase structure.

    Supports two modes:
      1. Kernel mode: uses a live AmbientKernel instance for runtime info
      2. Standalone mode: scans the filesystem directly (default)
    """

    def __init__(self, kernel: "AmbientKernel | None" = None, root: Path | None = None):
        self._kernel = kernel
        self._root = root or AMBIENT_ROOT
        self._subsystems: list[SubsystemNode] = []
        self._edges: list[dict[str, str]] = []
        self._built = False

    def build(self) -> "ArchitectureGraph":
        """Scan all subsystem modules and build the architecture graph."""
        logger.info("Building architecture graph from %s", self._root)
        start = time.monotonic()

        self._subsystems = []
        self._edges = []

        for subsystem_path in KNOWN_SUBSYSTEMS:
            subsystem_dir = self._root / subsystem_path
            if not subsystem_dir.is_dir():
                logger.warning("Subsystem directory not found: %s", subsystem_dir)
                continue

            subsystem_name = subsystem_path.replace("/", ".")
            modules = self._scan_subsystem_dir(subsystem_dir, subsystem_name)

            all_deps: set[str] = set()
            for mod in modules:
                for imp in mod.imports:
                    dep_subsystem = self._resolve_import_to_subsystem(imp)
                    if dep_subsystem and dep_subsystem != subsystem_name:
                        all_deps.add(dep_subsystem)
                        self._edges.append({
                            "from": subsystem_name,
                            "to": dep_subsystem,
                            "via": f"{mod.name} imports {imp}",
                        })

            node = SubsystemNode(
                name=subsystem_name,
                modules=modules,
                dependencies=sorted(all_deps),
                status="active",
            )
            self._subsystems.append(node)

        elapsed = (time.monotonic() - start) * 1000
        logger.info(
            "Architecture graph built: %d subsystems, %d modules, %d edges (%.1fms)",
            len(self._subsystems),
            sum(len(s.modules) for s in self._subsystems),
            len(self._edges),
            elapsed,
        )
        self._built = True
        return self

    def get_system_topology(self) -> dict[str, Any]:
        """Return a structured dict representing the full architecture tree."""
        self._ensure_built()
        return {
            "subsystems": {s.name: s.to_dict() for s in self._subsystems},
            "edges": self._edges,
            "summary": {
                "subsystem_count": len(self._subsystems),
                "module_count": sum(len(s.modules) for s in self._subsystems),
                "class_count": sum(
                    len(m.classes) for s in self._subsystems for m in s.modules
                ),
                "edge_count": len(self._edges),
            },
        }

    def get_subsystem(self, name: str) -> SubsystemNode | None:
        """Return details for a specific subsystem by name."""
        self._ensure_built()
        for s in self._subsystems:
            if s.name == name:
                return s
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serializable representation of the full architecture graph."""
        self._ensure_built()
        return {
            "root": str(self._root),
            "built": self._built,
            "topology": self.get_system_topology(),
        }

    def to_mermaid(self) -> str:
        """Generate a Mermaid diagram string of the architecture."""
        self._ensure_built()
        lines = ["graph TD"]

        for s in self._subsystems:
            safe_id = s.name.replace(".", "_")
            lines.append(f"    {safe_id}[{s.name}]")

        seen_edges: set[tuple[str, str]] = set()
        for edge in self._edges:
            from_id = edge["from"].replace(".", "_")
            to_id = edge["to"].replace(".", "_")
            pair = (from_id, to_id)
            if pair not in seen_edges:
                seen_edges.add(pair)
                lines.append(f"    {from_id} --> {to_id}")

        return "\n".join(lines)

    def snapshot(self) -> Path:
        """Save current state to state/topology_snapshots/ as timestamped JSON."""
        self._ensure_built()
        snapshot_dir = self._root / "state" / "topology_snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(timezone.utc)
        snap = TopologySnapshot(
            timestamp=ts.isoformat(),
            subsystems=self._subsystems,
            edges=self._edges,
            metadata={
                "root": str(self._root),
                "subsystem_count": len(self._subsystems),
                "module_count": sum(len(s.modules) for s in self._subsystems),
                "class_count": sum(
                    len(m.classes) for s in self._subsystems for m in s.modules
                ),
            },
        )

        filename = f"topology_{ts.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = snapshot_dir / filename

        filepath.write_text(
            json.dumps(snap.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Topology snapshot saved: %s", filepath)
        return filepath

    # ── Internal Methods ──────────────────────────────────────────────────

    def _ensure_built(self) -> None:
        if not self._built:
            self.build()

    def _scan_subsystem_dir(self, directory: Path, subsystem_name: str) -> list[ModuleNode]:
        """Scan all .py files in a subsystem directory."""
        modules: list[ModuleNode] = []

        for py_file in sorted(directory.rglob("*.py")):
            if py_file.name.startswith("__pycache__"):
                continue

            rel_path = py_file.relative_to(self._root)
            mod_name = py_file.stem

            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=str(py_file))
            except (SyntaxError, UnicodeDecodeError) as exc:
                logger.warning("Failed to parse %s: %s", py_file, exc)
                continue

            classes = self._extract_classes(tree)
            imports = self._extract_imports(tree)

            modules.append(ModuleNode(
                name=mod_name,
                path=str(rel_path),
                classes=classes,
                imports=imports,
            ))

        return modules

    def _extract_classes(self, tree: ast.Module) -> list[ClassNode]:
        """Extract class definitions from an AST."""
        classes: list[ClassNode] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            methods: list[str] = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not item.name.startswith("_"):
                        methods.append(item.name)

            bases: list[str] = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(ast.unparse(base))

            classes.append(ClassNode(
                name=node.name,
                methods=methods,
                base_classes=bases,
            ))

        return classes

    def _extract_imports(self, tree: ast.Module) -> list[str]:
        """Extract import paths from an AST."""
        imports: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return imports

    def _resolve_import_to_subsystem(self, import_path: str) -> str | None:
        """Map an import path to a known subsystem name."""
        subsystem_map = {
            "kernel": "kernel",
            "agents": "agents",
            "governance": "governance",
            "memory": "memory",
            "context": "context",
            "runtime.task_graph": "runtime.task_graph",
            "runtime": "runtime.task_graph",
            "somatic": "somatic",
            "observability": "observability",
        }

        for prefix, subsystem in subsystem_map.items():
            if import_path == prefix or import_path.startswith(prefix + "."):
                return subsystem

        return None
