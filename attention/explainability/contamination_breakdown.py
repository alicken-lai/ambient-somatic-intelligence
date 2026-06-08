"""
Contamination breakdown — explains identity/constitutional contamination signals.

Wraps the governance contamination guard to report whether external text carries
identity-override or constitutional-contamination signals. Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.external.contamination_guard import ContaminationGuard


class ContaminationBreakdown:
    """Transparent breakdown of external contamination signals."""

    def __init__(self) -> None:
        self.guard = ContaminationGuard()

    def breakdown(self, text: str) -> dict[str, Any]:
        verdict = self.guard.scan(text)

        summary = (
            f"Contamination {'detected' if verdict.contaminated else 'not detected'} "
            f"({len(verdict.signals)} signal(s), severity={verdict.severity:.4f})."
        )

        return {
            "advisory_only": True,
            "contaminated": verdict.contaminated,
            "signals": list(verdict.signals),
            "severity": round(verdict.severity, 4),
            "summary": summary,
        }
