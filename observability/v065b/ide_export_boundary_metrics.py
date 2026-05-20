"""IDE export boundary metrics — advisory header present."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from governance.external.external_rule_boundary import ADVISORY_HEADER

_RULES_DIR = Path(__file__).resolve().parents[2] / "hermes" / "rules" / "external"
_EXPORTS = (
    "cursor_external_rules.md",
    "vscode_external_rules.md",
    "codex_external_rules.md",
    "antigravity_external_rules.md",
)


@dataclass
class IdeExportBoundaryMetrics:
    boundary_rate: float = 1.0
    files_checked: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_rate": round(self.boundary_rate, 4),
            "files_checked": self.files_checked,
        }


def collect_ide_export_boundary_metrics() -> IdeExportBoundaryMetrics:
    passed = 0
    for name in _EXPORTS:
        path = _RULES_DIR / name
        if path.is_file() and ADVISORY_HEADER in path.read_text(encoding="utf-8"):
            passed += 1
    total = len(_EXPORTS)
    return IdeExportBoundaryMetrics(
        boundary_rate=passed / total if total else 0.0,
        files_checked=total,
    )
