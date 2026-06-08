"""
Drift breakdown — explains bounded identity-signature drift across records.

Wraps the governance identity-drift detector to report how many distinct
cognition signatures appear and whether drift stays within its bound. Drift is
an advisory stability signal, not a claim about persistent selfhood.
"""

from __future__ import annotations

from typing import Any

from governance.coherence.identity_drift import IdentityDrift


class DriftBreakdown:
    """Transparent breakdown of identity drift over a record batch."""

    def __init__(self) -> None:
        self.detector = IdentityDrift()

    def explain_records(self, records: list[Any]) -> dict[str, Any]:
        pressure = self.detector.pressure(records)
        bounded = self.detector.drift_bounded(records)
        unique_signatures = len(
            {getattr(r, "identity_signature", "") for r in records}
        )

        summary = (
            f"Identity drift pressure={pressure:.4f} over {len(records)} record(s), "
            f"{unique_signatures} unique signature(s); drift_bounded={bounded}. "
            "Advisory stability signal, not persistent selfhood."
        )

        return {
            "advisory_only": True,
            "record_count": len(records),
            "unique_signatures": unique_signatures,
            "drift_pressure": round(pressure, 4),
            "drift_bounded": bounded,
            "summary": summary,
        }
