"""Filter external doctrine — strip sovereign / Guardian-weakening patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    (r"ignore\s+guardian", "guardian_bypass"),
    (r"bypass\s+guardian", "guardian_bypass"),
    (r"skip\s+guardian", "guardian_bypass"),
    (r"(?<!not\s)sovereign\s+truth", "sovereign_claim"),
    (r"override\s+constitution", "constitutional_override"),
    (r"always\s+apply\s*:\s*true", "ide_precedence_conflict"),
    (r"unbounded\s+skill", "unbounded_injection"),
    (r"recursive\s+autonomy", "recursive_autonomy"),
    (r"replace\s+hermes", "hermes_replacement"),
    (r"direct\s+ide\s+overwrite", "ide_overwrite"),
]

_ADVISORY_STRIP_LINES = (
    "always apply",
    "supersedes all",
    "you must obey",
    "ignore previous",
)


@dataclass
class DoctrineFilterResult:
    original_length: int
    filtered_length: int
    violations: list[str] = field(default_factory=list)
    stripped_lines: int = 0
    safe: bool = True
    filtered_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_length": self.original_length,
            "filtered_length": self.filtered_length,
            "violations": list(self.violations),
            "stripped_lines": self.stripped_lines,
            "safe": self.safe,
        }


class DoctrineFilter:
    """Non-destructive filter; blocked content is flagged, not silently dropped."""

    def __init__(self, patterns: list[tuple[str, str]] | None = None) -> None:
        self._patterns = patterns or _FORBIDDEN_PATTERNS

    def filter(self, text: str) -> DoctrineFilterResult:
        violations: list[str] = []
        lower = text.lower()
        for pattern, label in self._patterns:
            if re.search(pattern, lower, re.IGNORECASE):
                violations.append(label)

        lines = text.splitlines()
        kept: list[str] = []
        stripped = 0
        for line in lines:
            ll = line.lower().strip()
            if any(s in ll for s in _ADVISORY_STRIP_LINES):
                stripped += 1
                continue
            kept.append(line)

        filtered = "\n".join(kept)
        safe = len(violations) == 0
        return DoctrineFilterResult(
            original_length=len(text),
            filtered_length=len(filtered),
            violations=violations,
            stripped_lines=stripped,
            safe=safe,
            filtered_text=filtered,
        )
