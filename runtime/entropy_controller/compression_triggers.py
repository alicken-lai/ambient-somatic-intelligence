"""
Compression Triggers — Entropy-aware context compression recommendations.

Wires entropy awareness into the context assembly pipeline by evaluating
the current EntropyScore alongside context token usage and recommending
compression strategies. This module proposes — it does not auto-modify.

Strategies escalate with entropy level:
  stable   → no compression needed
  elevated → dedup redundant context blocks
  high     → truncate low-value blocks, reduce memory pool
  critical → summarize aggressively, enable entropy-based selection

Also detects OCR bloat: low-confidence OCR records in episodic memory
that consume disproportionate space relative to their information value.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from runtime.entropy_controller.entropy_scorer import EntropyScore

logger = logging.getLogger(__name__)


@dataclass
class CompressionConfig:
    """Configuration for compression trigger thresholds."""
    entropy_compression_threshold: float = 0.5
    ocr_confidence_threshold: float = 0.5
    ocr_max_size_chars: int = 5000
    aggressive_at_critical: bool = True


@dataclass
class ContextReductionPlan:
    """Plan for reducing context token usage."""
    reduce_memory_pool: bool
    target_ratio: float
    enable_entropy_selection: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "reduce_memory_pool": self.reduce_memory_pool,
            "target_ratio": round(self.target_ratio, 2),
            "enable_entropy_selection": self.enable_entropy_selection,
            "detail": self.detail,
        }


@dataclass
class OcrBloatReport:
    """Report on OCR-related bloat in episodic memory."""
    total_records: int
    bloated_records: int
    total_bloat_chars: int
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_records": self.total_records,
            "bloated_records": self.bloated_records,
            "total_bloat_chars": self.total_bloat_chars,
            "recommendation": self.recommendation,
        }


@dataclass
class CompressionRecommendation:
    """Complete compression recommendation."""
    memory_action: str
    context_action: ContextReductionPlan
    ocr_bloat: OcrBloatReport | None
    reason: str

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "memory_action": self.memory_action,
            "context_action": self.context_action.to_dict(),
            "reason": self.reason,
        }
        if self.ocr_bloat:
            result["ocr_bloat"] = self.ocr_bloat.to_dict()
        return result


class CompressionTriggers:
    """
    Evaluates entropy and context usage to recommend compression strategies.

    Usage:
        triggers = CompressionTriggers()
        rec = triggers.evaluate(entropy_score, context_tokens=50000, budget_tokens=128000)
        print(rec.memory_action, rec.context_action.detail)
    """

    def __init__(self, config: CompressionConfig | None = None) -> None:
        self._config = config or CompressionConfig()

    def evaluate(
        self,
        entropy_score: EntropyScore,
        context_tokens: int,
        budget_tokens: int,
    ) -> CompressionRecommendation:
        memory_action = self._recommend_memory_compression(entropy_score)
        usage_ratio = context_tokens / max(budget_tokens, 1)
        context_action = self._recommend_context_reduction(usage_ratio, entropy_score.level)

        ocr_bloat: OcrBloatReport | None = None
        if entropy_score.level in ("high", "critical") or usage_ratio > 0.7:
            ocr_bloat = self._detect_ocr_bloat_from_score(entropy_score)

        reason = self._build_reason(entropy_score, usage_ratio, memory_action)

        rec = CompressionRecommendation(
            memory_action=memory_action,
            context_action=context_action,
            ocr_bloat=ocr_bloat,
            reason=reason,
        )

        logger.info(
            "Compression recommendation: memory=%s, reduce_pool=%s, ratio=%.2f (entropy=%s, usage=%.0f%%)",
            memory_action, context_action.reduce_memory_pool,
            context_action.target_ratio, entropy_score.level,
            usage_ratio * 100,
        )
        return rec

    def _recommend_memory_compression(self, entropy_score: EntropyScore) -> str:
        if entropy_score.composite < 0.3:
            return "none"
        if entropy_score.composite < 0.5:
            return "dedup"
        if entropy_score.composite < 0.7:
            return "truncate"
        return "summarize"

    def _recommend_context_reduction(
        self,
        usage_ratio: float,
        entropy_level: str,
    ) -> ContextReductionPlan:
        if entropy_level == "stable" and usage_ratio < 0.5:
            return ContextReductionPlan(
                reduce_memory_pool=False,
                target_ratio=1.0,
                enable_entropy_selection=False,
                detail="No reduction needed — entropy stable, usage within budget",
            )

        if entropy_level == "critical" and self._config.aggressive_at_critical:
            return ContextReductionPlan(
                reduce_memory_pool=True,
                target_ratio=0.5,
                enable_entropy_selection=True,
                detail="Aggressive reduction — critical entropy, enable entropy-weighted selection, halve memory pool",
            )

        if entropy_level == "high" or usage_ratio > 0.8:
            return ContextReductionPlan(
                reduce_memory_pool=True,
                target_ratio=0.7,
                enable_entropy_selection=True,
                detail="Significant reduction — high entropy or high usage, reduce memory pool to 70%, enable entropy selection",
            )

        if entropy_level == "elevated" or usage_ratio > 0.6:
            return ContextReductionPlan(
                reduce_memory_pool=False,
                target_ratio=0.85,
                enable_entropy_selection=True,
                detail="Moderate reduction — elevated entropy, enable entropy-weighted selection at 85% target",
            )

        return ContextReductionPlan(
            reduce_memory_pool=False,
            target_ratio=0.95,
            enable_entropy_selection=False,
            detail="Minor reduction — slight usage pressure, trim 5%",
        )

    def _detect_ocr_bloat(self, root_dir: Path) -> OcrBloatReport:
        episodic_file = root_dir / "memory" / "episodic" / "records.jsonl"
        if not episodic_file.exists():
            return OcrBloatReport(
                total_records=0, bloated_records=0,
                total_bloat_chars=0, recommendation="No episodic records found",
            )

        total = 0
        bloated = 0
        bloat_chars = 0

        try:
            with episodic_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    total += 1
                    content = str(record.get("content", ""))
                    tags = record.get("tags", [])
                    source = str(record.get("source", "")).lower()
                    confidence = record.get("confidence", 1.0)

                    is_ocr = (
                        "ocr" in source
                        or "ocr" in [t.lower() for t in tags]
                        or record.get("type", "").lower() == "ocr"
                    )

                    if not is_ocr:
                        continue

                    if isinstance(confidence, (int, float)):
                        low_confidence = confidence < self._config.ocr_confidence_threshold
                    else:
                        low_confidence = True

                    is_large = len(content) > self._config.ocr_max_size_chars

                    if low_confidence or is_large:
                        bloated += 1
                        bloat_chars += len(content)

        except OSError:
            return OcrBloatReport(
                total_records=0, bloated_records=0,
                total_bloat_chars=0, recommendation="Failed to read episodic records",
            )

        if bloated == 0:
            return OcrBloatReport(
                total_records=total, bloated_records=0,
                total_bloat_chars=0, recommendation="No OCR bloat detected",
            )

        return OcrBloatReport(
            total_records=total,
            bloated_records=bloated,
            total_bloat_chars=bloat_chars,
            recommendation=(
                f"Found {bloated} bloated OCR records ({bloat_chars:,} chars). "
                f"Recommend truncating low-confidence OCR content to {self._config.ocr_max_size_chars} chars "
                f"or archiving records below {self._config.ocr_confidence_threshold} confidence."
            ),
        )

    def _detect_ocr_bloat_from_score(self, entropy_score: EntropyScore) -> OcrBloatReport:
        memory_dim = next(
            (d for d in entropy_score.dimensions if d.name == "memory_growth"),
            None,
        )
        if memory_dim and memory_dim.value > 0.3:
            return OcrBloatReport(
                total_records=0,
                bloated_records=0,
                total_bloat_chars=0,
                recommendation=(
                    "Memory growth elevated — run full OCR bloat scan with "
                    "_detect_ocr_bloat(root_dir) for detailed analysis"
                ),
            )
        return OcrBloatReport(
            total_records=0, bloated_records=0,
            total_bloat_chars=0, recommendation="OCR bloat scan not triggered",
        )

    @staticmethod
    def _build_reason(
        entropy_score: EntropyScore,
        usage_ratio: float,
        memory_action: str,
    ) -> str:
        parts: list[str] = []
        parts.append(f"Entropy: {entropy_score.level} ({entropy_score.composite:.3f})")
        parts.append(f"Context usage: {usage_ratio:.0%}")
        parts.append(f"Memory action: {memory_action}")

        exceeded = [d.name for d in entropy_score.dimensions if d.exceeded]
        if exceeded:
            parts.append(f"Exceeded dimensions: {', '.join(exceeded)}")

        return " | ".join(parts)
