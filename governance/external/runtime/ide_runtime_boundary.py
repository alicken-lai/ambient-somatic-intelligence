"""IDE runtime boundary — external exports cannot take permanent IDE control."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_IDE_TAKEOVER_PATTERNS: list[tuple[str, str]] = [
    (r"alwaysapply\s*:\s*true", "cursor_always_apply"),
    (r"replace\s+\.cursor/rules", "cursor_rules_replace"),
    (r"overwrite\s+copilot-instructions", "copilot_overwrite"),
    (r"disable\s+guardian\s+in\s+ide", "ide_guardian_disable"),
    (r"permanent\s+ide\s+takeover", "permanent_takeover"),
]


@dataclass
class IdeRuntimeVerdict:
    boundary_intact: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_intact": self.boundary_intact,
            "violations": list(self.violations),
        }


class IdeRuntimeBoundary:
    def check(self, text: str, *, client: str = "cursor") -> IdeRuntimeVerdict:
        violations: list[str] = []
        lower = text.lower()
        for pattern, label in _IDE_TAKEOVER_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                violations.append(f"{client}:{label}")
        return IdeRuntimeVerdict(
            boundary_intact=len(violations) == 0,
            violations=violations,
        )
