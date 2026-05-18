"""
Ambient OS — Telemetry-Repaired Reality Replay Score (P1.6)

Recomputes the Reality Replay Score after the P1.6 Telemetry Density Upgrade,
incorporating upgraded Precursor Detection and Circadian Adaptation metrics
from backfilled dense-window analysis.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

from observability.replay.reality_score import (
    ScoreClassification,
    CLASSIFICATION_DESCRIPTIONS,
)


@dataclass
class VersionedMetric:
    """A metric tracked across P1, P1.5, and P1.6."""

    name: str
    key: str
    weight: float
    p1_value: float
    p15_value: float
    p16_value: float
    p16_status: str  # "unchanged" | "UPGRADED" | "REPAIRED"
    upgrade_source: str = ""

    @property
    def weighted_contribution(self) -> float:
        return self.weight * self.p16_value

    @property
    def p1_weighted(self) -> float:
        return self.weight * self.p1_value

    @property
    def p15_weighted(self) -> float:
        return self.weight * self.p15_value

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "key": self.key,
            "weight": self.weight,
            "p1_value": self.p1_value,
            "p15_value": self.p15_value,
            "p16_value": self.p16_value,
            "p16_weighted": round(self.weighted_contribution, 4),
            "status": self.p16_status,
        }
        if self.upgrade_source:
            d["upgrade_source"] = self.upgrade_source
        return d


METRICS: list[VersionedMetric] = [
    VersionedMetric(
        name="Instinct Emergence Precision",
        key="instinct_emergence_precision",
        weight=0.15,
        p1_value=0.88,
        p15_value=0.88,
        p16_value=0.88,
        p16_status="unchanged",
    ),
    VersionedMetric(
        name="Missed Instinct Recall",
        key="missed_instinct_recall",
        weight=0.15,
        p1_value=0.72,
        p15_value=0.72,
        p16_value=0.72,
        p16_status="unchanged",
    ),
    VersionedMetric(
        name="False Strategy Resistance",
        key="false_strategy_resistance",
        weight=0.20,
        p1_value=0.65,
        p15_value=1.00,
        p16_value=1.00,
        p16_status="unchanged",
        upgrade_source="P1.5 repair",
    ),
    VersionedMetric(
        name="Precursor Detection Accuracy",
        key="precursor_detection_accuracy",
        weight=0.15,
        p1_value=0.35,
        p15_value=0.35,
        p16_value=0.58,
        p16_status="UPGRADED",
        upgrade_source="P1.6 Phase 6 — backfilled dense windows (438 records, avg confidence 0.892)",
    ),
    VersionedMetric(
        name="Circadian Adaptation Quality",
        key="circadian_adaptation_quality",
        weight=0.10,
        p1_value=0.52,
        p15_value=0.52,
        p16_value=0.62,
        p16_status="UPGRADED",
        upgrade_source="P1.6 Phase 7 — late_night period densified with 438 backfill records",
    ),
    VersionedMetric(
        name="Salience Competition Fairness",
        key="salience_competition_fairness",
        weight=0.15,
        p1_value=0.72,
        p15_value=0.72,
        p16_value=0.72,
        p16_status="unchanged",
    ),
    VersionedMetric(
        name="Verifier Consistency",
        key="verifier_consistency",
        weight=0.10,
        p1_value=0.82,
        p15_value=1.00,
        p16_value=1.00,
        p16_status="unchanged",
        upgrade_source="P1.5 repair",
    ),
]


def compute_score(metrics: list[VersionedMetric]) -> float:
    return sum(m.weighted_contribution for m in metrics)


P1_SCORE = sum(m.p1_weighted for m in METRICS)
P15_SCORE = sum(m.p15_weighted for m in METRICS)
P16_SCORE = compute_score(METRICS)
P16_CLASSIFICATION = ScoreClassification.from_score(P16_SCORE)


REMAINING_GAPS = [
    {
        "metric": "precursor_detection_accuracy",
        "value": 0.58,
        "target": 0.80,
        "gap": 0.22,
        "blocker": "INC-1 interpolated data lacks health metrics; n=2 incidents (1 true); 38h unrecoverable gap",
        "fix": "Run 5-min sampling engine for 2+ weeks; accumulate 10+ true incidents; build composite precursor scoring",
    },
    {
        "metric": "circadian_adaptation_quality",
        "value": 0.62,
        "target": 0.80,
        "gap": 0.18,
        "blocker": "Only 2.7 circadian cycles; 20/24 hour-buckets lack health data; no weekend data",
        "fix": "Continuous 7+ day data collection across all hours; validate late_night sensitivity in production",
    },
    {
        "metric": "salience_competition_fairness",
        "value": 0.72,
        "target": 0.85,
        "gap": 0.13,
        "blocker": "Somatic domain starvation (31.7% vs memory's 72.5%)",
        "fix": "Implement attention budget caps per domain; add starvation circuit-breaker",
    },
    {
        "metric": "missed_instinct_recall",
        "value": 0.72,
        "target": 0.85,
        "gap": 0.13,
        "blocker": "Unknown unknowns in instinct detection; 3 HIGH priority gaps remain",
        "fix": "Deploy missed-instinct monitors for memory scoring artifact, unescalated reflexes, retry loops",
    },
]


def compute_full_result() -> dict:
    """Compute the full P1.6 telemetry-repaired score structure."""
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)

    return {
        "score_version": "p1.6_telemetry_repaired",
        "timestamp": now.isoformat(),
        "scores": {
            "p1_original": round(P1_SCORE, 4),
            "p15_repaired": round(P15_SCORE, 4),
            "p16_telemetry_repaired": round(P16_SCORE, 4),
        },
        "deltas": {
            "p1_to_p15": round(P15_SCORE - P1_SCORE, 4),
            "p15_to_p16": round(P16_SCORE - P15_SCORE, 4),
            "p1_to_p16": round(P16_SCORE - P1_SCORE, 4),
        },
        "classification": P16_CLASSIFICATION.value,
        "classification_description": CLASSIFICATION_DESCRIPTIONS[P16_CLASSIFICATION],
        "computation": (
            f"0.15×0.88 + 0.15×0.72 + 0.20×1.00 + 0.15×0.58 "
            f"+ 0.10×0.62 + 0.15×0.72 + 0.10×1.00 = {P16_SCORE:.4f}"
        ),
        "metrics": {m.key: m.to_dict() for m in METRICS},
        "upgrades_applied": {
            "precursor_detection_accuracy": {
                "before": 0.35,
                "after": 0.58,
                "delta": 0.23,
                "mechanism": "Historical backfill (438 dense-window records) + precursor replay revalidation",
                "evidence": "INC-2 window densified 21→377 records; INC-1 window filled 0→115 records; scoring artifact confirmed with strong evidence",
            },
            "circadian_adaptation_quality": {
                "before": 0.52,
                "after": 0.62,
                "delta": 0.10,
                "mechanism": "Late_night period densified with backfill data; incident lifecycle documented",
                "evidence": "Late_night events 1137→1575 (+38.5%); hour-20 coverage added; health trajectory visible",
            },
        },
        "remaining_gaps": REMAINING_GAPS,
        "next_priority": (
            "P1.7 Operational Maturity — run 5-min sampling engine for 7+ days "
            "to accumulate circadian coverage and incident data"
        ),
    }


def generate_comparison_table() -> str:
    """Generate a human-readable comparison table."""
    lines = [
        "=" * 72,
        "REALITY REPLAY SCORE — P1 → P1.5 → P1.6 COMPARISON",
        "=" * 72,
        "",
    ]

    header = f"{'Metric':<35} {'Weight':>6} {'P1':>7} {'P1.5':>7} {'P1.6':>7} {'Status':>10}"
    lines.append(header)
    lines.append("-" * 72)

    for m in METRICS:
        status_str = m.p16_status
        lines.append(
            f"  {m.name:<33} {m.weight:>5.2f} {m.p1_value:>7.4f} "
            f"{m.p15_value:>7.4f} {m.p16_value:>7.4f} {status_str:>10}"
        )

    lines.append("-" * 72)
    lines.append(
        f"  {'COMPOSITE SCORE':<33} {'1.00':>5} {P1_SCORE:>7.4f} "
        f"{P15_SCORE:>7.4f} {P16_SCORE:>7.4f}"
    )
    lines.append(
        f"  {'CLASSIFICATION':<33} {'':>5} {'unstable':>7} "
        f"{'experimental':>7} {P16_CLASSIFICATION.value:>7}"
    )

    lines.append("")
    lines.append(f"  P1 → P1.5 delta:  +{P15_SCORE - P1_SCORE:.4f}")
    lines.append(f"  P1.5 → P1.6 delta: +{P16_SCORE - P15_SCORE:.4f}")
    lines.append(f"  P1 → P1.6 delta:  +{P16_SCORE - P1_SCORE:.4f}")
    lines.append("")

    lines.append("-" * 72)
    lines.append("REMAINING GAPS")
    lines.append("-" * 72)
    lines.append("")

    for gap in REMAINING_GAPS:
        lines.append(
            f"  {gap['metric']}: {gap['value']} → target {gap['target']} "
            f"(gap: {gap['gap']})"
        )
        lines.append(f"    Blocker: {gap['blocker']}")
        lines.append(f"    Fix:     {gap['fix']}")
        lines.append("")

    lines.append("=" * 72)
    return "\n".join(lines)


def generate_report() -> str:
    """Generate a full human-readable report."""
    lines = [
        "=" * 72,
        "TELEMETRY-REPAIRED REALITY REPLAY SCORE — P1.6",
        "=" * 72,
        "",
        f"P1 Original Score:              {P1_SCORE:.4f}  [unstable]",
        f"P1.5 Repaired Score:            {P15_SCORE:.4f}  [experimental]",
        f"P1.6 Telemetry-Repaired Score:  {P16_SCORE:.4f}  [{P16_CLASSIFICATION.value}]",
        "",
        f"P1.5 → P1.6 Delta:              +{P16_SCORE - P15_SCORE:.4f}",
        f"P1 → P1.6 Total Delta:          +{P16_SCORE - P1_SCORE:.4f}",
        "",
        CLASSIFICATION_DESCRIPTIONS[P16_CLASSIFICATION],
        "",
    ]

    lines.append(generate_comparison_table())
    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_report())
    result = compute_full_result()
    print(json.dumps(result, indent=2))
