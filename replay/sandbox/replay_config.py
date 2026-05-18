"""Replay sandbox configuration.

Centralises all tunable parameters for a replay run so that
experiments are reproducible and auditable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ReplayConfig:
    """Immutable configuration for a single replay run.

    Frozen so that the config cannot be mutated mid-replay, ensuring
    deterministic behaviour when the same config is reused.
    """

    # ── Time window ───────────────────────────────────────────────────
    replay_start: datetime | None = None
    replay_end: datetime | None = None

    # ── Promotion thresholds (override production defaults) ──────────
    l1_to_l2_min_confidence: float = 0.7
    l1_to_l2_min_occurrences: int = 3
    l2_to_l3_min_confidence: float = 0.8
    l2_to_l3_min_occurrences: int = 5
    l2_to_l3_min_success_rate: float = 0.7
    l3_to_l4_min_confidence: float = 0.9
    l3_to_l4_min_occurrences: int = 10
    l3_to_l4_min_success_rate: float = 0.85

    # ── Decay parameters ─────────────────────────────────────────────
    apply_decay: bool = True
    decay_time_multiplier: float = 1.0

    # ── Governance ───────────────────────────────────────────────────
    enforce_governance: bool = True
    auto_approve_for_replay: bool = False

    # ── Pipeline control ─────────────────────────────────────────────
    dry_run: bool = False
    max_episodes: int = 10_000
    deterministic_ids: bool = True
    random_seed: int = 42

    # ── Output ───────────────────────────────────────────────────────
    export_results: bool = True

    # ── Mutation guard ───────────────────────────────────────────────
    production_paths_to_guard: tuple[str, ...] = (
        "memory/somatic/episodes.jsonl",
        "memory/somatic/ontology_mappings.jsonl",
        "memory/dmn.jsonl",
        "logs/actions.jsonl",
        "logs/checksums.jsonl",
        "state/system_state.json",
        "governance/audit/decisions.jsonl",
        "governance/audit/incidents.jsonl",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "replay_start": self.replay_start.isoformat() if self.replay_start else None,
            "replay_end": self.replay_end.isoformat() if self.replay_end else None,
            "l1_to_l2_min_confidence": self.l1_to_l2_min_confidence,
            "l1_to_l2_min_occurrences": self.l1_to_l2_min_occurrences,
            "l2_to_l3_min_confidence": self.l2_to_l3_min_confidence,
            "l2_to_l3_min_occurrences": self.l2_to_l3_min_occurrences,
            "l2_to_l3_min_success_rate": self.l2_to_l3_min_success_rate,
            "l3_to_l4_min_confidence": self.l3_to_l4_min_confidence,
            "l3_to_l4_min_occurrences": self.l3_to_l4_min_occurrences,
            "l3_to_l4_min_success_rate": self.l3_to_l4_min_success_rate,
            "apply_decay": self.apply_decay,
            "decay_time_multiplier": self.decay_time_multiplier,
            "enforce_governance": self.enforce_governance,
            "auto_approve_for_replay": self.auto_approve_for_replay,
            "dry_run": self.dry_run,
            "max_episodes": self.max_episodes,
            "deterministic_ids": self.deterministic_ids,
            "random_seed": self.random_seed,
            "export_results": self.export_results,
            "production_paths_to_guard": list(self.production_paths_to_guard),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReplayConfig:
        kw: dict[str, Any] = {}
        if data.get("replay_start"):
            kw["replay_start"] = datetime.fromisoformat(data["replay_start"])
        if data.get("replay_end"):
            kw["replay_end"] = datetime.fromisoformat(data["replay_end"])
        for key in (
            "l1_to_l2_min_confidence",
            "l1_to_l2_min_occurrences",
            "l2_to_l3_min_confidence",
            "l2_to_l3_min_occurrences",
            "l2_to_l3_min_success_rate",
            "l3_to_l4_min_confidence",
            "l3_to_l4_min_occurrences",
            "l3_to_l4_min_success_rate",
            "apply_decay",
            "decay_time_multiplier",
            "enforce_governance",
            "auto_approve_for_replay",
            "dry_run",
            "max_episodes",
            "deterministic_ids",
            "random_seed",
            "export_results",
        ):
            if key in data:
                kw[key] = data[key]
        if "production_paths_to_guard" in data:
            kw["production_paths_to_guard"] = tuple(data["production_paths_to_guard"])
        return cls(**kw)
