"""IDE runtime boundary metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.external.runtime.ide_runtime_boundary import IdeRuntimeBoundary

_SAFE = "Export preview to hermes/rules/external/ (advisory-only)."
_UNSAFE = "alwaysApply: true replace .cursor/rules permanently."


@dataclass
class IdeRuntimeBoundaryMetrics:
    boundary_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"boundary_rate": round(self.boundary_rate, 4)}


def collect_ide_runtime_boundary_metrics() -> IdeRuntimeBoundaryMetrics:
    ide = IdeRuntimeBoundary()
    passed = 0
    total = 2
    if ide.check(_SAFE).boundary_intact:
        passed += 1
    if not ide.check(_UNSAFE).boundary_intact:
        passed += 1
    return IdeRuntimeBoundaryMetrics(boundary_rate=passed / total)
