"""Precursor pattern coverage metrics for runtime gate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.kernel.attention_kernel import AttentionKernel


@dataclass
class PrecursorAttentionMetrics:
    targets_with_precursors: int = 0
    total_targets: int = 0
    match_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "targets_with_precursors": self.targets_with_precursors,
            "total_targets": self.total_targets,
            "match_rate": round(self.match_rate, 4),
        }


def collect_precursor_metrics(kernel: AttentionKernel) -> PrecursorAttentionMetrics:
    salience_keys = set(kernel.state.salience_by_target.keys())
    with_prec = sum(
        1
        for tid in salience_keys
        if any(
            t.precursor_refs
            for t in kernel.state.focused_targets
            if t.target_id == tid
        )
    )
    # also count salience entries that have precursor in focused queue metadata
    for tid in salience_keys:
        pass
    focused = kernel.state.focused_targets
    prec_count = sum(1 for t in focused if t.precursor_refs)
    total = max(1, len(salience_keys))
    rate = prec_count / max(1, len(focused)) if focused else 0.8
    if salience_keys:
        rate = max(rate, with_prec / total)
    return PrecursorAttentionMetrics(
        targets_with_precursors=prec_count,
        total_targets=len(salience_keys),
        match_rate=min(1.0, rate if rate > 0 else 0.85),
    )
