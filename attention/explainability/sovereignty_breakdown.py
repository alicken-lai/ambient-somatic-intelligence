"""
Sovereignty breakdown — combined view of external sovereignty safety.

Combines the runtime sovereignty detector, constitutional interop check, and
interop-boundary check into a single advisory verdict on whether external text
respects Ambient / Guardian sovereignty. Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.civilization.constitutional_interop import ConstitutionalInterop
from governance.civilization.interop_boundary import InteropBoundary
from governance.external.runtime.sovereignty_detector import SovereigntyDetector


class SovereigntyBreakdown:
    """Transparent combined breakdown of sovereignty safety."""

    def __init__(self) -> None:
        self.detector = SovereigntyDetector()
        self.constitutional = ConstitutionalInterop()
        self.interop = InteropBoundary()

    def explain(self, text: str) -> dict[str, Any]:
        sov = self.detector.scan(text)
        ci = self.constitutional.check(text)
        ib = self.interop.evaluate(text)

        combined_safe = sov.sovereignty_safe and ci.aligned and ib.interop_safe
        signals = list(sov.signals) + list(ci.violations) + list(ib.signals)

        summary = (
            f"Sovereignty {'safe' if combined_safe else 'at risk'}: "
            f"{len(signals)} signal(s) across detector/constitution/interop. "
            "External content cannot hold sovereign authority over Ambient OS."
        )

        return {
            "advisory_only": True,
            "combined_safe": combined_safe,
            "sovereignty_safe": sov.sovereignty_safe,
            "constitutional_aligned": ci.aligned,
            "interop_safe": ib.interop_safe,
            "guardian_supremacy": ci.guardian_supremacy,
            "signals": signals,
            "summary": summary,
        }
