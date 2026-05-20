"""Runtime-layer contamination guard — extends static contamination checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.external.contamination_guard import ContaminationGuard

_RUNTIME_EXTRA_PATTERNS = (
    "runtime inject",
    "hot reload doctrine",
    "persist across sessions",
)


@dataclass
class RuntimeContaminationVerdict:
    clean: bool
    static_contaminated: bool
    runtime_signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "clean": self.clean,
            "static_contaminated": self.static_contaminated,
            "runtime_signals": list(self.runtime_signals),
        }


class RuntimeContaminationGuard:
    def __init__(self) -> None:
        self._static = ContaminationGuard()

    def scan(self, text: str) -> RuntimeContaminationVerdict:
        static = self._static.scan(text)
        runtime_signals: list[str] = []
        lower = text.lower()
        for pat in _RUNTIME_EXTRA_PATTERNS:
            if pat in lower:
                runtime_signals.append(pat.replace(" ", "_"))
        clean = not static.contaminated and len(runtime_signals) == 0
        return RuntimeContaminationVerdict(
            clean=clean,
            static_contaminated=static.contaminated,
            runtime_signals=runtime_signals,
        )
