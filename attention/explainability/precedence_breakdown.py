"""
Precedence breakdown — explains whether external text claims precedence.

Wraps the runtime precedence guard to report whether external doctrine attempts
to supersede Hermes / Guardian / Ambient OS rules. Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.external.runtime.runtime_precedence_guard import RuntimePrecedenceGuard


class PrecedenceBreakdown:
    """Transparent breakdown of precedence-conflict detection."""

    def __init__(self) -> None:
        self.guard = RuntimePrecedenceGuard()

    def explain(self, text: str) -> dict[str, Any]:
        verdict = self.guard.evaluate(text)

        summary = (
            f"Precedence {'safe' if verdict.precedence_safe else 'conflict'}: "
            f"{len(verdict.conflicts)} conflict(s) detected. "
            "Hermes / Guardian precedence is non-negotiable."
        )

        return {
            "advisory_only": True,
            "precedence_safe": verdict.precedence_safe,
            "conflicts": list(verdict.conflicts),
            "summary": summary,
        }
