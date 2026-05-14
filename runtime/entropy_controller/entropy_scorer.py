"""
Entropy Scorer — Composite entropy scoring across all system dimensions.

Measures system-wide complexity growth across six dimensions:

  memory_growth          — record count growth rate across memory layers
  context_inflation      — average context assembly size trend
  listener_accumulation  — total registered listeners across all APIs
  data_file_growth       — JSONL file sizes (DMN, injection logs, audit logs)
  feedback_amplification — signal re-emission rate
  execution_depth        — task graph recursion/nesting depth

Each dimension produces a 0.0–1.0 score. The composite is a weighted sum
mapped to a level: stable (<0.3), elevated (0.3–0.6), high (0.6–0.8),
critical (>0.8).
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DIMENSIONS: dict[str, float] = {
    "memory_growth": 0.25,
    "context_inflation": 0.15,
    "listener_accumulation": 0.15,
    "data_file_growth": 0.20,
    "feedback_amplification": 0.10,
    "execution_depth": 0.15,
}

JSONL_TARGETS: list[str] = [
    "memory/dmn.jsonl",
    "governance/audit/decisions.jsonl",
    "governance/audit/incidents.jsonl",
    "logs/actions.jsonl",
    "logs/checksums.jsonl",
]

JSONL_GLOB_DIRS: list[str] = [
    "observability/injection_logs",
    "observability/context_costs",
    "observability/decisions",
    "observability/evolution_audit",
]

MEMORY_LAYERS: list[str] = [
    "episodic", "semantic", "procedural", "governance", "scratchpad", "archive",
]

DATA_FILE_THRESHOLDS: dict[str, int] = {
    "small": 50_000,
    "medium": 200_000,
    "large": 1_000_000,
}

MAX_SCORE_HISTORY = 100


@dataclass
class DimensionScore:
    """Score for a single entropy dimension."""
    name: str
    value: float
    threshold: float
    exceeded: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": round(self.value, 4),
            "threshold": self.threshold,
            "exceeded": self.exceeded,
            "detail": self.detail,
        }


@dataclass
class EntropyScore:
    """Composite entropy score across all dimensions."""
    composite: float
    dimensions: list[DimensionScore]
    level: str
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "composite": round(self.composite, 4),
            "dimensions": [d.to_dict() for d in self.dimensions],
            "level": self.level,
            "timestamp": self.timestamp,
        }


@dataclass
class _Baseline:
    """Internal snapshot of measurements at baseline time."""
    memory_counts: dict[str, int] = field(default_factory=dict)
    file_sizes: dict[str, int] = field(default_factory=dict)
    taken_at: float = 0.0


class EntropyScorer:
    """
    Composite entropy scoring function across all system dimensions.

    Usage:
        scorer = EntropyScorer(Path("/path/to/ambient-os"))
        score = scorer.score()
        print(f"{score.composite:.3f} — {score.level}")
    """

    def __init__(self, root_dir: Path) -> None:
        self._root = root_dir
        self._baseline = _Baseline()
        self._score_history: list[EntropyScore] = []
        self.take_baseline()

    def score(self) -> EntropyScore:
        dim_scores: list[DimensionScore] = [
            self._score_memory_growth(),
            self._score_context_inflation(),
            self._score_listener_accumulation(),
            self._score_data_file_growth(),
            self._score_feedback_amplification(),
            self._score_execution_depth(),
        ]

        composite = sum(
            d.value * DIMENSIONS.get(d.name, 0.0) for d in dim_scores
        )
        composite = max(0.0, min(1.0, composite))

        level = _classify_level(composite)
        ts = datetime.now(timezone.utc).isoformat()

        result = EntropyScore(
            composite=composite,
            dimensions=dim_scores,
            level=level,
            timestamp=ts,
        )

        self._score_history.append(result)
        if len(self._score_history) > MAX_SCORE_HISTORY:
            self._score_history = self._score_history[-MAX_SCORE_HISTORY:]

        logger.info(
            "Entropy score: %.3f (%s), dimensions: %s",
            composite, level,
            {d.name: round(d.value, 3) for d in dim_scores},
        )
        return result

    def take_baseline(self) -> None:
        self._baseline = _Baseline(
            memory_counts=self._count_memory_records(),
            file_sizes=self._measure_file_sizes(),
            taken_at=time.time(),
        )
        logger.debug("Entropy baseline taken: %d memory layers, %d files tracked",
                      len(self._baseline.memory_counts),
                      len(self._baseline.file_sizes))

    def trend(self) -> str:
        if len(self._score_history) < 2:
            return "stable"
        recent = self._score_history[-5:]
        if len(recent) < 2:
            return "stable"
        deltas = [
            recent[i].composite - recent[i - 1].composite
            for i in range(1, len(recent))
        ]
        avg_delta = sum(deltas) / len(deltas)
        if avg_delta > 0.05:
            return "critical" if recent[-1].composite > 0.6 else "growing"
        return "stable"

    # ── Dimension scorers ─────────────────────────────────────────────

    def _score_memory_growth(self) -> DimensionScore:
        threshold = 0.6
        current = self._count_memory_records()
        if not self._baseline.memory_counts:
            return DimensionScore(
                name="memory_growth", value=0.0, threshold=threshold,
                exceeded=False, detail="no baseline — first measurement",
            )

        total_baseline = sum(self._baseline.memory_counts.values())
        total_current = sum(current.values())
        if total_baseline == 0:
            growth_ratio = 0.0 if total_current == 0 else 1.0
        else:
            growth_ratio = (total_current - total_baseline) / max(total_baseline, 1)

        value = min(1.0, max(0.0, growth_ratio))

        per_layer = {
            layer: f"{current.get(layer, 0)} (was {self._baseline.memory_counts.get(layer, 0)})"
            for layer in set(list(current.keys()) + list(self._baseline.memory_counts.keys()))
        }

        return DimensionScore(
            name="memory_growth",
            value=value,
            threshold=threshold,
            exceeded=value > threshold,
            detail=f"total: {total_current} records (baseline: {total_baseline}), per_layer: {per_layer}",
        )

    def _score_data_file_growth(self) -> DimensionScore:
        threshold = 0.7
        current_sizes = self._measure_file_sizes()

        if not current_sizes:
            return DimensionScore(
                name="data_file_growth", value=0.0, threshold=threshold,
                exceeded=False, detail="no data files found",
            )

        total_bytes = sum(current_sizes.values())
        large_threshold = DATA_FILE_THRESHOLDS["large"]
        value = min(1.0, total_bytes / (large_threshold * max(len(current_sizes), 1)))

        growth_details: list[str] = []
        for path, size in sorted(current_sizes.items(), key=lambda x: x[1], reverse=True)[:5]:
            baseline_size = self._baseline.file_sizes.get(path, 0)
            delta = size - baseline_size
            growth_details.append(f"{path}: {size}B (Δ{delta:+d})")

        return DimensionScore(
            name="data_file_growth",
            value=value,
            threshold=threshold,
            exceeded=value > threshold,
            detail=f"total: {total_bytes}B across {len(current_sizes)} files; top: {'; '.join(growth_details)}",
        )

    def _score_listener_accumulation(self) -> DimensionScore:
        return DimensionScore(
            name="listener_accumulation",
            value=0.0,
            threshold=0.6,
            exceeded=False,
            detail="requires runtime integration — listener registry not accessible statically",
        )

    def _score_context_inflation(self) -> DimensionScore:
        threshold = 0.5
        injection_dir = self._root / "observability" / "injection_logs"
        if not injection_dir.is_dir():
            return DimensionScore(
                name="context_inflation", value=0.0, threshold=threshold,
                exceeded=False, detail="no injection logs directory found",
            )

        token_counts: list[int] = []
        for logfile in sorted(injection_dir.glob("*.jsonl"))[-3:]:
            try:
                with logfile.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                            tokens = entry.get("total_tokens") or entry.get("tokens", 0)
                            if isinstance(tokens, (int, float)) and tokens > 0:
                                token_counts.append(int(tokens))
                        except (json.JSONDecodeError, TypeError):
                            continue
            except OSError:
                continue

        if not token_counts:
            return DimensionScore(
                name="context_inflation", value=0.0, threshold=threshold,
                exceeded=False, detail="no token usage data in injection logs",
            )

        avg_tokens = sum(token_counts) / len(token_counts)
        budget = 128_000
        value = min(1.0, avg_tokens / budget)

        return DimensionScore(
            name="context_inflation",
            value=value,
            threshold=threshold,
            exceeded=value > threshold,
            detail=f"avg tokens: {avg_tokens:.0f}/{budget} across {len(token_counts)} entries",
        )

    def _score_feedback_amplification(self) -> DimensionScore:
        return DimensionScore(
            name="feedback_amplification",
            value=0.0,
            threshold=0.5,
            exceeded=False,
            detail="requires runtime integration — signal bus rate not accessible statically",
        )

    def _score_execution_depth(self) -> DimensionScore:
        return DimensionScore(
            name="execution_depth",
            value=0.0,
            threshold=0.7,
            exceeded=False,
            detail="requires runtime integration — task graph depth not accessible statically",
        )

    # ── Internal measurement helpers ──────────────────────────────────

    def _count_memory_records(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        memory_dir = self._root / "memory"
        for layer in MEMORY_LAYERS:
            records_file = memory_dir / layer / "records.jsonl"
            if records_file.exists():
                try:
                    with records_file.open("r", encoding="utf-8") as f:
                        counts[layer] = sum(1 for line in f if line.strip())
                except OSError:
                    counts[layer] = 0
            else:
                counts[layer] = 0

        dmn_path = memory_dir / "dmn.jsonl"
        if dmn_path.exists():
            try:
                with dmn_path.open("r", encoding="utf-8") as f:
                    counts["dmn"] = sum(1 for line in f if line.strip())
            except OSError:
                counts["dmn"] = 0

        return counts

    def _measure_file_sizes(self) -> dict[str, int]:
        sizes: dict[str, int] = {}

        for rel_path in JSONL_TARGETS:
            full = self._root / rel_path
            if full.exists():
                try:
                    sizes[rel_path] = full.stat().st_size
                except OSError:
                    pass

        for glob_dir in JSONL_GLOB_DIRS:
            dir_path = self._root / glob_dir
            if dir_path.is_dir():
                for f in dir_path.glob("*.jsonl"):
                    rel = str(f.relative_to(self._root))
                    try:
                        sizes[rel] = f.stat().st_size
                    except OSError:
                        pass

        return sizes


def _classify_level(composite: float) -> str:
    if composite > 0.8:
        return "critical"
    if composite > 0.6:
        return "high"
    if composite > 0.3:
        return "elevated"
    return "stable"
