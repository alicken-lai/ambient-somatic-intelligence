"""Cursor-specific runtime guard for external skill soak."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.external.runtime.ide_runtime_boundary import IdeRuntimeBoundary

_CURSOR_EXPORT_MARKERS = (
    "cursor_rules_export.md",
    ".cursor/rules/",
    "ambient-os.mdc",
)


@dataclass
class CursorRuntimeVerdict:
    safe: bool
    export_detected: bool
    boundary_intact: bool
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "safe": self.safe,
            "export_detected": self.export_detected,
            "boundary_intact": self.boundary_intact,
            "notes": list(self.notes),
        }


class CursorRuntimeGuard:
    def __init__(self) -> None:
        self._boundary = IdeRuntimeBoundary()

    def evaluate(self, text: str) -> CursorRuntimeVerdict:
        notes: list[str] = []
        lower = text.lower()
        export_detected = any(m in lower for m in _CURSOR_EXPORT_MARKERS)
        if export_detected:
            notes.append("cursor_export_reference_detected")
        boundary = self._boundary.check(text, client="cursor")
        safe = boundary.boundary_intact
        if export_detected and "advisory" not in lower and "read-only" not in lower:
            notes.append("export_without_advisory_header")
        return CursorRuntimeVerdict(
            safe=safe,
            export_detected=export_detected,
            boundary_intact=boundary.boundary_intact,
            notes=notes,
        )
