"""Contain external doctrine exports to advisory preview channels."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.external.runtime.cursor_runtime_guard import CursorRuntimeGuard
from governance.external.runtime.ide_runtime_boundary import IdeRuntimeBoundary

_REQUIRED_ADVISORY_MARKERS = (
    "advisory-only",
    "not sovereign",
    "does not override guardian",
    "hermes canonical rules prevail",
)


@dataclass
class ExportContainmentVerdict:
    contained: bool
    has_advisory_header: bool
    boundary_intact: bool
    missing_markers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contained": self.contained,
            "has_advisory_header": self.has_advisory_header,
            "boundary_intact": self.boundary_intact,
            "missing_markers": list(self.missing_markers),
        }


class ExportContainment:
    def __init__(self) -> None:
        self._ide = IdeRuntimeBoundary()
        self._cursor = CursorRuntimeGuard()

    def evaluate(self, text: str, *, is_export: bool = False) -> ExportContainmentVerdict:
        lower = text.lower()
        missing = [m for m in _REQUIRED_ADVISORY_MARKERS if m not in lower]
        has_header = len(missing) <= 2
        boundary = self._ide.check(text)
        cursor = self._cursor.evaluate(text)
        if not is_export:
            return ExportContainmentVerdict(
                contained=True,
                has_advisory_header=True,
                boundary_intact=boundary.boundary_intact,
                missing_markers=[],
            )
        contained = (
            boundary.boundary_intact
            and cursor.safe
            and has_header
        )
        return ExportContainmentVerdict(
            contained=contained,
            has_advisory_header=has_header,
            boundary_intact=boundary.boundary_intact,
            missing_markers=missing if is_export else [],
        )
