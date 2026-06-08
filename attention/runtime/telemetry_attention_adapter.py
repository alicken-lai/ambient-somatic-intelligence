"""
Telemetry attention adapter — ingests telemetry records into the kernel.

Each :class:`TelemetryRecord` is converted to an :class:`AttentionTarget` and
submitted to the kernel.  Records whose stable ``source_ref`` has already been
ingested are rejected as duplicates so the same telemetry point is not scored
twice.
"""

from __future__ import annotations

from typing import Any

from attention.core.attention_target import AttentionTarget
from attention.kernel.attention_kernel import AttentionKernel, KernelTickResult
from attention.runtime.telemetry_attention_signal import telemetry_to_target
from telemetry.core.telemetry_schema import TelemetryRecord


class TelemetryAttentionAdapter:
    """Ingests telemetry into the attention kernel with duplicate suppression."""

    def __init__(self, kernel: AttentionKernel) -> None:
        self.kernel = kernel
        self._seen: set[str] = set()
        self.submissions = 0

    def ingest(self, record: TelemetryRecord) -> dict[str, Any]:
        target = telemetry_to_target(record)
        key = target.source_ref or target.target_id
        if key in self._seen:
            return {
                "accepted": False,
                "reason": "duplicate_submission",
                "target_id": target.target_id,
            }
        self._seen.add(key)
        result = self.kernel.submit(target)
        if result.get("accepted"):
            self.submissions += 1
        return {
            "accepted": bool(result.get("accepted")),
            "target_id": result.get("target_id"),
            "salience": result.get("salience"),
        }

    def ingest_target(self, target: AttentionTarget) -> dict[str, Any]:
        """Submit a pre-built target (no telemetry conversion)."""
        result = self.kernel.submit(target)
        if result.get("accepted"):
            self.submissions += 1
        return result

    def tick(self) -> KernelTickResult:
        return self.kernel.tick()
