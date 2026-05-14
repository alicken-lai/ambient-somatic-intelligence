"""Decay Engine — prevents stale knowledge from polluting the system.

All decay is observable (reports) and explainable (reasons).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .confidence_model import ConfidenceModel
from .decay_rules import DecayRule, DECAY_RULE_REGISTRY
from .layer_definition import MemoryLayer


@dataclass
class DecayReport:
    entry_id: str
    layer: MemoryLayer
    previous_confidence: float
    new_confidence: float
    decay_reason: str
    below_threshold: bool
    recommended_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "layer": self.layer.value,
            "previous_confidence": self.previous_confidence,
            "new_confidence": self.new_confidence,
            "decay_reason": self.decay_reason,
            "below_threshold": self.below_threshold,
            "recommended_action": self.recommended_action,
        }


def _last_access_time(entry: Any) -> datetime | None:
    for attr in ("last_accessed", "last_validated", "last_executed", "last_applied"):
        val = getattr(entry, attr, None)
        if val is not None:
            return val
    return None


def _recommend_action(new_confidence: float, rule: DecayRule) -> str:
    if new_confidence <= rule.min_confidence:
        return "remove"
    margin = new_confidence - rule.min_confidence
    if margin < 0.1:
        return "archive"
    return "retain"


class DecayEngine:
    """Applies time decay, inactivity decay, contradiction, and failure penalties."""

    def __init__(
        self,
        rules: list[DecayRule],
        confidence_model: ConfidenceModel,
    ) -> None:
        self._rules = {r.layer: r for r in rules}
        self._confidence_model = confidence_model

    def _get_rule(self, layer: MemoryLayer) -> DecayRule | None:
        return self._rules.get(layer)

    def apply_time_decay(
        self, entries: list[Any], current_time: datetime
    ) -> list[DecayReport]:
        """Apply time-based exponential decay to all entries."""
        reports: list[DecayReport] = []
        for entry in entries:
            rule = self._get_rule(entry.layer)
            if rule is None:
                continue

            elapsed = (current_time - entry.timestamp).total_seconds() / 86400.0
            if elapsed <= 0:
                continue

            prev = entry.confidence
            new_conf = prev * math.exp(-rule.base_rate_per_day * elapsed)
            new_conf = max(new_conf, rule.min_confidence)

            self._confidence_model._make_update(entry, new_conf, "decay", floor=rule.min_confidence)

            reports.append(
                DecayReport(
                    entry_id=entry.entry_id,
                    layer=entry.layer,
                    previous_confidence=prev,
                    new_confidence=entry.confidence,
                    decay_reason="time_decay",
                    below_threshold=entry.confidence <= rule.min_confidence,
                    recommended_action=_recommend_action(entry.confidence, rule),
                )
            )
        return reports

    def apply_inactivity_decay(
        self, entries: list[Any], current_time: datetime
    ) -> list[DecayReport]:
        """Apply accelerated decay for entries inactive beyond their threshold."""
        reports: list[DecayReport] = []
        for entry in entries:
            rule = self._get_rule(entry.layer)
            if rule is None:
                continue

            last_access = _last_access_time(entry)
            if last_access is None:
                last_access = entry.timestamp

            days_inactive = (current_time - last_access).total_seconds() / 86400.0
            if days_inactive <= rule.inactivity_threshold_days:
                continue

            prev = entry.confidence
            effective_rate = rule.base_rate_per_day * rule.inactivity_multiplier
            new_conf = prev * math.exp(-effective_rate * days_inactive)
            new_conf = max(new_conf, rule.min_confidence)

            self._confidence_model._make_update(entry, new_conf, "decay", floor=rule.min_confidence)

            reports.append(
                DecayReport(
                    entry_id=entry.entry_id,
                    layer=entry.layer,
                    previous_confidence=prev,
                    new_confidence=entry.confidence,
                    decay_reason="inactivity",
                    below_threshold=entry.confidence <= rule.min_confidence,
                    recommended_action=_recommend_action(entry.confidence, rule),
                )
            )
        return reports

    def apply_contradiction(
        self, entry: Any, evidence: str
    ) -> DecayReport:
        """Apply contradiction penalty to a specific entry."""
        rule = self._get_rule(entry.layer)
        prev = entry.confidence

        self._confidence_model.update_on_contradiction(entry, evidence, rule=rule)

        min_conf = rule.min_confidence if rule else 0.0
        return DecayReport(
            entry_id=entry.entry_id,
            layer=entry.layer,
            previous_confidence=prev,
            new_confidence=entry.confidence,
            decay_reason="contradiction",
            below_threshold=entry.confidence <= min_conf,
            recommended_action=_recommend_action(entry.confidence, rule) if rule else "retain",
        )

    def apply_failed_reuse(
        self, entry: Any, context: str
    ) -> DecayReport:
        """Apply failure penalty when entry was used but produced a bad result."""
        rule = self._get_rule(entry.layer)
        prev = entry.confidence

        self._confidence_model.update_on_failure(entry, context, rule=rule)

        min_conf = rule.min_confidence if rule else 0.0
        return DecayReport(
            entry_id=entry.entry_id,
            layer=entry.layer,
            previous_confidence=prev,
            new_confidence=entry.confidence,
            decay_reason="failed_reuse",
            below_threshold=entry.confidence <= min_conf,
            recommended_action=_recommend_action(entry.confidence, rule) if rule else "retain",
        )

    def sweep(
        self, entries: list[Any], current_time: datetime
    ) -> list[DecayReport]:
        """Full decay sweep: time + inactivity + threshold check."""
        reports: list[DecayReport] = []
        for entry in entries:
            rule = self._get_rule(entry.layer)
            if rule is None:
                continue

            elapsed = (current_time - entry.timestamp).total_seconds() / 86400.0
            if elapsed <= 0:
                continue

            prev = entry.confidence
            rate = rule.base_rate_per_day

            last_access = _last_access_time(entry)
            if last_access is not None:
                days_inactive = (current_time - last_access).total_seconds() / 86400.0
            else:
                days_inactive = elapsed

            if days_inactive > rule.inactivity_threshold_days:
                rate *= rule.inactivity_multiplier

            new_conf = prev * math.exp(-rate * elapsed)
            new_conf = max(new_conf, rule.min_confidence)

            reason = "time_decay"
            if days_inactive > rule.inactivity_threshold_days:
                reason = "inactivity"

            self._confidence_model._make_update(entry, new_conf, "decay", floor=rule.min_confidence)

            reports.append(
                DecayReport(
                    entry_id=entry.entry_id,
                    layer=entry.layer,
                    previous_confidence=prev,
                    new_confidence=entry.confidence,
                    decay_reason=reason,
                    below_threshold=entry.confidence <= rule.min_confidence,
                    recommended_action=_recommend_action(entry.confidence, rule),
                )
            )
        return reports

    def get_at_risk_entries(
        self, entries: list[Any], current_time: datetime
    ) -> list[DecayReport]:
        """Find entries approaching removal threshold (within 0.1 margin)."""
        at_risk: list[DecayReport] = []
        for entry in entries:
            rule = self._get_rule(entry.layer)
            if rule is None:
                continue
            margin = entry.confidence - rule.min_confidence
            if margin <= 0.1:
                at_risk.append(
                    DecayReport(
                        entry_id=entry.entry_id,
                        layer=entry.layer,
                        previous_confidence=entry.confidence,
                        new_confidence=entry.confidence,
                        decay_reason="at_risk",
                        below_threshold=entry.confidence <= rule.min_confidence,
                        recommended_action=_recommend_action(entry.confidence, rule),
                    )
                )
        return at_risk

    def generate_report(self, reports: list[DecayReport]) -> str:
        """Generate a human-readable decay report."""
        if not reports:
            return "Decay sweep: no entries affected."

        lines = [f"Decay Report — {len(reports)} entries affected", "=" * 50]
        by_action: dict[str, list[DecayReport]] = {}
        for r in reports:
            by_action.setdefault(r.recommended_action, []).append(r)

        for action in ("remove", "archive", "retain"):
            group = by_action.get(action, [])
            if not group:
                continue
            lines.append(f"\n[{action.upper()}] — {len(group)} entries")
            for r in group:
                lines.append(
                    f"  {r.entry_id} (L{r.layer}) "
                    f"{r.previous_confidence:.3f} → {r.new_confidence:.3f} "
                    f"({r.decay_reason})"
                )

        return "\n".join(lines)
