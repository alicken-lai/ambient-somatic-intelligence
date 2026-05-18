"""Replay Observability — metrics, tracing, and audit for replay runs.

Aggregates telemetry from all sandbox components into a unified view
of the replay session.  All results are exportable as JSON for
subsequent analysis phases.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from memory.ontology.layer_definition import MemoryLayer

from .replay_config import ReplayConfig


@dataclass
class ReplaySpan:
    """A single traced operation within the replay pipeline."""

    span_id: str
    operation: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "ok"  # "ok" | "error" | "skipped"

    def finish(self, status: str = "ok") -> None:
        self.ended_at = datetime.now(timezone.utc)
        self.duration_ms = (
            (self.ended_at - self.started_at).total_seconds() * 1000
        )
        self.status = status

    def to_dict(self) -> dict[str, Any]:
        return {
            "span_id": self.span_id,
            "operation": self.operation,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_ms": round(self.duration_ms, 2),
            "metadata": self.metadata,
            "status": self.status,
        }


class ReplayObservability:
    """Unified observability layer for replay sessions.

    Responsibilities:
      - Trace every pipeline phase as a :class:`ReplaySpan`.
      - Aggregate promotion / decay / verification metrics.
      - Maintain a chronological audit log.
      - Compute replay health metrics.
      - Export everything as JSON.
    """

    def __init__(self, config: ReplayConfig) -> None:
        self._config = config
        self._spans: list[ReplaySpan] = []
        self._span_counter: int = 0
        self._audit: list[dict[str, Any]] = []
        self._counters: dict[str, int] = {}
        self._started_at: datetime = datetime.now(timezone.utc)

    # ── Tracing ──────────────────────────────────────────────────────

    def start_span(
        self,
        operation: str,
        metadata: dict[str, Any] | None = None,
    ) -> ReplaySpan:
        """Begin a new trace span. Call ``span.finish()`` when done."""
        self._span_counter += 1
        span = ReplaySpan(
            span_id=f"span-{self._span_counter:04d}",
            operation=operation,
            started_at=datetime.now(timezone.utc),
            metadata=metadata or {},
        )
        self._spans.append(span)
        return span

    # ── Counters ─────────────────────────────────────────────────────

    def increment(self, metric: str, amount: int = 1) -> None:
        self._counters[metric] = self._counters.get(metric, 0) + amount

    def get_counter(self, metric: str) -> int:
        return self._counters.get(metric, 0)

    # ── Audit logging ────────────────────────────────────────────────

    def log(self, event: str, details: dict[str, Any] | None = None) -> None:
        self._audit.append({
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **(details or {}),
        })

    # ── Collect from components ───────────────────────────────────────

    def collect_promotion_results(self, results: dict[str, Any]) -> None:
        """Ingest results from ReplayPromotionEngine.export_results()."""
        self.increment("promotions_total", results.get("total_records", 0))
        self.increment("promotions_approved", results.get("approved", 0))
        self.increment("promotions_rejected", results.get("rejected", 0))
        self.log("promotion_results_collected", {
            "total": results.get("total_records", 0),
            "approved": results.get("approved", 0),
            "rejected": results.get("rejected", 0),
        })

    def collect_decay_results(self, results: dict[str, Any]) -> None:
        """Ingest results from ReplayDecayEngine.export_results()."""
        self.increment("decay_total", results.get("total_decayed", 0))
        self.increment("decay_removed", results.get("entries_removed", 0))
        self.log("decay_results_collected", {
            "total": results.get("total_decayed", 0),
            "removed": results.get("entries_removed", 0),
        })

    def collect_verification_results(self, results: dict[str, Any]) -> None:
        """Ingest results from ReplayVerifier.export_results()."""
        self.increment("verifications_total", results.get("total_verifications", 0))
        self.increment("verifications_allowed", results.get("allowed", 0))
        self.increment("verifications_blocked", results.get("blocked", 0))
        self.log("verification_results_collected", {
            "total": results.get("total_verifications", 0),
            "allowed": results.get("allowed", 0),
            "blocked": results.get("blocked", 0),
        })

    def collect_store_summary(self, summary: dict[str, int]) -> None:
        """Ingest layer summary from ReplayMemoryStore.layer_summary()."""
        for layer_name, count in summary.items():
            self._counters[f"store_{layer_name}"] = count
        self.log("store_summary_collected", summary)

    # ── Health metrics ───────────────────────────────────────────────

    def compute_health_metrics(self) -> dict[str, Any]:
        """Compute replay-specific health metrics."""
        total_prom = self.get_counter("promotions_total")
        approved = self.get_counter("promotions_approved")
        blocked = self.get_counter("verifications_blocked")

        promotion_rate = approved / total_prom if total_prom > 0 else 0.0
        block_rate = blocked / total_prom if total_prom > 0 else 0.0

        total_spans = len(self._spans)
        error_spans = sum(1 for s in self._spans if s.status == "error")
        pipeline_health = 1.0 - (error_spans / total_spans) if total_spans > 0 else 1.0

        elapsed = (datetime.now(timezone.utc) - self._started_at).total_seconds()

        return {
            "promotion_rate": round(promotion_rate, 4),
            "governance_block_rate": round(block_rate, 4),
            "pipeline_health": round(pipeline_health, 4),
            "total_spans": total_spans,
            "error_spans": error_spans,
            "elapsed_seconds": round(elapsed, 2),
            "counters": dict(self._counters),
        }

    # ── Export ────────────────────────────────────────────────────────

    def export_results(self) -> dict[str, Any]:
        """Export the full observability state as a JSON-serialisable dict."""
        return {
            "config": self._config.to_dict(),
            "health_metrics": self.compute_health_metrics(),
            "spans": [s.to_dict() for s in self._spans],
            "counters": dict(self._counters),
            "audit_log": list(self._audit),
            "started_at": self._started_at.isoformat(),
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }

    def export_to_file(self, path: str | Path) -> str:
        """Write the full results to a JSON file. Returns the path written."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.export_results()
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        return str(path)

    # ── Mutation guard reporting ──────────────────────────────────────

    def compute_file_checksums(self, root: Path) -> dict[str, str]:
        """Compute SHA-256 checksums for guarded production files."""
        checksums: dict[str, str] = {}
        for rel in self._config.production_paths_to_guard:
            full = root / rel
            if full.exists():
                h = hashlib.sha256()
                with full.open("rb") as fh:
                    for chunk in iter(lambda: fh.read(8192), b""):
                        h.update(chunk)
                checksums[rel] = h.hexdigest()
            else:
                checksums[rel] = "FILE_NOT_FOUND"
        return checksums

    def verify_no_mutation(
        self,
        root: Path,
        before_checksums: dict[str, str],
    ) -> tuple[bool, list[str]]:
        """Assert that no guarded production file was modified.

        Returns ``(clean, list_of_mutated_files)``.
        """
        after = self.compute_file_checksums(root)
        mutated: list[str] = []
        for path, before_hash in before_checksums.items():
            after_hash = after.get(path, "MISSING")
            if before_hash != after_hash:
                mutated.append(path)
        clean = len(mutated) == 0
        self.log("mutation_guard_check", {
            "clean": clean,
            "mutated_files": mutated,
        })
        return clean, mutated
