"""Replay Runner — orchestrates a full replay session.

This is the main entry point for the Reality Replay sandbox.  It:
  1. Snapshots production file checksums (mutation guard).
  2. Loads historical data from the data catalog.
  3. Initialises all sandbox components via dependency injection.
  4. Runs the replay pipeline: ingest → promotion → verification → decay.
  5. Collects and exports results.
  6. Validates that no production files were mutated.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from memory.ontology.confidence_model import ConfidenceModel
from memory.ontology.decay_rules import DECAY_RULES
from memory.ontology.episodic_schema import EpisodicEntry
from memory.ontology.instinct_schema import InstinctEntry
from memory.ontology.layer_definition import MemoryLayer
from memory.ontology.promotion_rules import PROMOTION_RULES
from memory.ontology.skill_schema import SkillMemoryEntry

from .replay_config import ReplayConfig
from .replay_decay_engine import ReplayDecayEngine
from .replay_memory_store import ReplayMemoryStore
from .replay_observability import ReplayObservability
from .replay_promotion_engine import ReplayPromotionEngine
from .replay_verifier import ReplayVerifier

logger = logging.getLogger(__name__)


@dataclass
class ReplayRunResult:
    """Final output of a complete replay run."""

    run_id: str
    config: ReplayConfig
    started_at: datetime
    finished_at: datetime | None = None
    success: bool = False
    mutation_clean: bool = False
    mutated_files: list[str] = field(default_factory=list)
    store_summary: dict[str, int] = field(default_factory=dict)
    promotion_summary: dict[str, Any] = field(default_factory=dict)
    decay_summary: dict[str, Any] = field(default_factory=dict)
    verification_summary: dict[str, Any] = field(default_factory=dict)
    health_metrics: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "config": self.config.to_dict(),
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "success": self.success,
            "mutation_clean": self.mutation_clean,
            "mutated_files": self.mutated_files,
            "store_summary": self.store_summary,
            "promotion_summary": self.promotion_summary,
            "decay_summary": self.decay_summary,
            "verification_summary": self.verification_summary,
            "health_metrics": self.health_metrics,
            "errors": self.errors,
        }


class ReplayRunner:
    """Orchestrates a full replay session inside the sandbox.

    Usage::

        config = ReplayConfig(auto_approve_for_replay=True)
        runner = ReplayRunner(config, workspace_root=Path("."))
        result = runner.run(episodes_path="memory/somatic/episodes.jsonl")
        print(json.dumps(result.to_dict(), indent=2))
    """

    def __init__(
        self,
        config: ReplayConfig,
        workspace_root: Path | str = ".",
    ) -> None:
        self._config = config
        self._root = Path(workspace_root).resolve()

        self._confidence_model = ConfidenceModel()
        self._store = ReplayMemoryStore()
        self._promoter = ReplayPromotionEngine(
            store=self._store,
            config=self._config,
            rules=list(PROMOTION_RULES),
            confidence_model=self._confidence_model,
        )
        self._decayer = ReplayDecayEngine(
            store=self._store,
            config=self._config,
            rules=list(DECAY_RULES),
            confidence_model=self._confidence_model,
        )
        self._verifier = ReplayVerifier(config=self._config)
        self._observability = ReplayObservability(config=self._config)

    # ── Public API ────────────────────────────────────────────────────

    def run(
        self,
        episodes_path: str | Path | None = None,
        extra_data: dict[str, list[dict[str, Any]]] | None = None,
    ) -> ReplayRunResult:
        """Execute a complete replay pipeline.

        Parameters
        ----------
        episodes_path:
            Path to a JSONL file of historical episodes to ingest
            into L1.
        extra_data:
            Optional dict mapping layer names (``"L2_INSTINCT"`` etc.)
            to lists of entry dicts to pre-populate those layers.
        """
        run_id = datetime.now(timezone.utc).strftime("replay-%Y%m%d-%H%M%S")
        result = ReplayRunResult(
            run_id=run_id,
            config=self._config,
            started_at=datetime.now(timezone.utc),
        )

        # ── Step 0: Snapshot production files ────────────────────────
        span = self._observability.start_span("mutation_guard_snapshot")
        before_checksums = self._observability.compute_file_checksums(self._root)
        span.finish()

        try:
            # ── Step 1: Ingest historical data ───────────────────────
            self._phase_ingest(episodes_path, extra_data)

            # ── Step 2: Promotion pipeline ───────────────────────────
            self._phase_promote()

            # ── Step 3: Governance verification ──────────────────────
            self._phase_verify()

            # ── Step 4: Decay sweep ──────────────────────────────────
            if self._config.apply_decay:
                self._phase_decay()

            result.success = True

        except Exception as exc:
            logger.exception("Replay pipeline failed: %s", exc)
            result.errors.append(str(exc))
            result.success = False

        # ── Step 5: Collect results ──────────────────────────────────
        self._observability.collect_promotion_results(self._promoter.export_results())
        self._observability.collect_decay_results(self._decayer.export_results())
        self._observability.collect_verification_results(self._verifier.export_results())
        self._observability.collect_store_summary(self._store.layer_summary())

        result.store_summary = self._store.layer_summary()
        result.promotion_summary = self._promoter.export_results()
        result.decay_summary = self._decayer.export_results()
        result.verification_summary = self._verifier.export_results()
        result.health_metrics = self._observability.compute_health_metrics()

        # ── Step 6: Mutation guard check ─────────────────────────────
        span = self._observability.start_span("mutation_guard_verify")
        clean, mutated = self._observability.verify_no_mutation(
            self._root, before_checksums
        )
        result.mutation_clean = clean
        result.mutated_files = mutated
        span.finish()

        if not clean:
            msg = f"MUTATION DETECTED in production files: {mutated}"
            logger.error(msg)
            result.errors.append(msg)
            result.success = False

        result.finished_at = datetime.now(timezone.utc)

        # ── Step 7: Export ───────────────────────────────────────────
        if self._config.export_results:
            self._export(result)

        return result

    # ── Pipeline phases ──────────────────────────────────────────────

    def _phase_ingest(
        self,
        episodes_path: str | Path | None,
        extra_data: dict[str, list[dict[str, Any]]] | None,
    ) -> None:
        span = self._observability.start_span("ingest")

        if episodes_path:
            full_path = self._root / episodes_path
            loaded = self._store.load_episodes_from_jsonl(
                full_path,
                max_entries=self._config.max_episodes,
                time_start=self._config.replay_start,
                time_end=self._config.replay_end,
            )
            self._observability.increment("episodes_loaded", loaded)
            self._observability.log("episodes_loaded", {
                "path": str(full_path),
                "count": loaded,
            })

        if extra_data:
            layer_map = {lyr.name: lyr for lyr in MemoryLayer}
            for layer_name, entries in extra_data.items():
                layer = layer_map.get(layer_name)
                if layer is None:
                    continue
                count = self._store.ingest_entries(entries, layer)
                self._observability.increment("extra_data_loaded", count)

        span.finish()

    def _phase_promote(self) -> None:
        """Run promotion scanning across L1 → L2 → L3."""
        span = self._observability.start_span("promotion")

        for source_layer, entry_cls in [
            (MemoryLayer.L1_EPISODIC, EpisodicEntry),
            (MemoryLayer.L2_INSTINCT, InstinctEntry),
            (MemoryLayer.L3_SKILL, SkillMemoryEntry),
        ]:
            replay_entries = self._store.get_all(source_layer)
            if not replay_entries:
                continue

            typed_entries = self._materialize_entries(replay_entries, entry_cls)
            if not typed_entries:
                continue

            records = self._promoter.process_layer(typed_entries, source_layer)
            self._observability.log("promotion_phase", {
                "source_layer": source_layer.value,
                "entries_scanned": len(typed_entries),
                "decisions": len(records),
            })

        span.finish()

    def _phase_verify(self) -> None:
        """Verify all promotion decisions through governance."""
        span = self._observability.start_span("verification")

        for record in self._promoter.records:
            if record.result.approved:
                self._verifier.verify_promotion(record.candidate)

        span.finish()

    def _phase_decay(self) -> None:
        """Apply decay across all layers in the store."""
        span = self._observability.start_span("decay")

        now = self._config.replay_end or datetime.now(timezone.utc)
        reports = self._decayer.process_all_layers(current_time=now)
        self._observability.log("decay_phase", {
            "total_reports": len(reports),
        })

        span.finish()

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _materialize_entries(
        replay_entries: list[Any],
        entry_cls: type,
    ) -> list[Any]:
        """Try to deserialise ReplayEntry payloads into typed entry objects."""
        result: list[Any] = []
        for re in replay_entries:
            payload = re.payload if hasattr(re, "payload") else {}
            if not payload:
                continue
            try:
                entry = entry_cls.from_dict(payload)
                result.append(entry)
            except (KeyError, TypeError, ValueError):
                continue
        return result

    def _export(self, result: ReplayRunResult) -> None:
        """Write results to replay/sandbox/results/<run_id>.json."""
        out_dir = self._root / "replay" / "sandbox" / "results"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{result.run_id}.json"
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(result.to_dict(), fh, indent=2, ensure_ascii=False, default=str)
        self._observability.log("results_exported", {"path": str(out_path)})
        logger.info("Replay results exported to %s", out_path)

    # ── Accessors for external inspection ────────────────────────────

    @property
    def store(self) -> ReplayMemoryStore:
        return self._store

    @property
    def promoter(self) -> ReplayPromotionEngine:
        return self._promoter

    @property
    def decayer(self) -> ReplayDecayEngine:
        return self._decayer

    @property
    def verifier(self) -> ReplayVerifier:
        return self._verifier

    @property
    def observability(self) -> ReplayObservability:
        return self._observability
