"""
Ambient OS — Matured Reality Replay Score (P1.7)

Recomputes the Reality Replay Score using ONLY real data (no interpolation).
Shows the P1 → P1.5 → P1.6 → P1.7 score progression with honest
real-data-only assessment for precursor detection and circadian adaptation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

from observability.replay.reality_score import (
    ScoreClassification,
    CLASSIFICATION_DESCRIPTIONS,
)


@dataclass
class VersionedMetricP17:
    """A metric tracked across P1, P1.5, P1.6, and P1.7."""

    name: str
    key: str
    weight: float
    p1_value: float
    p15_value: float
    p16_value: float
    p17_value: float
    p17_status: str
    p17_source: str = ""

    @property
    def weighted_p17(self) -> float:
        return self.weight * self.p17_value

    @property
    def weighted_p1(self) -> float:
        return self.weight * self.p1_value

    @property
    def weighted_p15(self) -> float:
        return self.weight * self.p15_value

    @property
    def weighted_p16(self) -> float:
        return self.weight * self.p16_value

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "key": self.key,
            "weight": self.weight,
            "p1": self.p1_value,
            "p15": self.p15_value,
            "p16": self.p16_value,
            "p17": self.p17_value,
            "p17_weighted": round(self.weighted_p17, 4),
            "status": self.p17_status,
        }
        if self.p17_source:
            d["p17_source"] = self.p17_source
        return d


METRICS_P17: list[VersionedMetricP17] = [
    VersionedMetricP17(
        name="Instinct Emergence Precision",
        key="instinct_emergence_precision",
        weight=0.15,
        p1_value=0.88, p15_value=0.88, p16_value=0.88, p17_value=0.88,
        p17_status="unchanged",
        p17_source="Phase 1C — all original data was real",
    ),
    VersionedMetricP17(
        name="Missed Instinct Recall",
        key="missed_instinct_recall",
        weight=0.15,
        p1_value=0.72, p15_value=0.72, p16_value=0.72, p17_value=0.72,
        p17_status="unchanged",
        p17_source="Phase 1D — all original data was real",
    ),
    VersionedMetricP17(
        name="False Strategy Resistance",
        key="false_strategy_resistance",
        weight=0.20,
        p1_value=0.65, p15_value=1.00, p16_value=1.00, p17_value=1.00,
        p17_status="unchanged (P1.5 repair)",
        p17_source="Code-level enforcement modules — data-independent",
    ),
    VersionedMetricP17(
        name="Precursor Detection Accuracy",
        key="precursor_detection_accuracy",
        weight=0.15,
        p1_value=0.35, p15_value=0.35, p16_value=0.58, p17_value=0.48,
        p17_status="REVISED (real-data-only)",
        p17_source="P1.7 Phase 5 — excludes 121 interpolated records; adds daemon baseline bonus",
    ),
    VersionedMetricP17(
        name="Circadian Adaptation Quality",
        key="circadian_adaptation_quality",
        weight=0.10,
        p1_value=0.52, p15_value=0.52, p16_value=0.62, p17_value=0.58,
        p17_status="REVISED (real-data-only)",
        p17_source="P1.7 Phase 6 — 18/24 hour coverage but uniform daemon-era behavior reduces differentiation",
    ),
    VersionedMetricP17(
        name="Salience Competition Fairness",
        key="salience_competition_fairness",
        weight=0.15,
        p1_value=0.72, p15_value=0.72, p16_value=0.72, p17_value=0.73,
        p17_status="marginal improvement",
        p17_source="P1.7 Phase 7 — daemon-era shows balanced event processing",
    ),
    VersionedMetricP17(
        name="Verifier Consistency",
        key="verifier_consistency",
        weight=0.10,
        p1_value=0.82, p15_value=1.00, p16_value=1.00, p17_value=1.00,
        p17_status="unchanged (P1.5 repair)",
        p17_source="Code-level enforcement modules — data-independent",
    ),
]


def compute_p17_score() -> float:
    return sum(m.weighted_p17 for m in METRICS_P17)


P1_SCORE = sum(m.weighted_p1 for m in METRICS_P17)
P15_SCORE = sum(m.weighted_p15 for m in METRICS_P17)
P16_SCORE = sum(m.weighted_p16 for m in METRICS_P17)
P17_SCORE = compute_p17_score()
P17_CLASSIFICATION = ScoreClassification.from_score(P17_SCORE)


def compute_full_result() -> dict:
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)

    return {
        "score_version": "p1.7_matured_real_data_only",
        "generated_at": now.isoformat(),
        "data_policy": "REAL DATA ONLY — no interpolation, no synthetic augmentation",
        "scores": {
            "p1_original": round(P1_SCORE, 4),
            "p15_repaired": round(P15_SCORE, 4),
            "p16_telemetry_repaired": round(P16_SCORE, 4),
            "p17_matured_real_data": round(P17_SCORE, 4),
        },
        "deltas": {
            "p1_to_p15": round(P15_SCORE - P1_SCORE, 4),
            "p15_to_p16": round(P16_SCORE - P15_SCORE, 4),
            "p16_to_p17": round(P17_SCORE - P16_SCORE, 4),
            "p1_to_p17": round(P17_SCORE - P1_SCORE, 4),
        },
        "classification": P17_CLASSIFICATION.value,
        "classification_description": CLASSIFICATION_DESCRIPTIONS[P17_CLASSIFICATION],
        "computation": (
            f"0.15×0.88 + 0.15×0.72 + 0.20×1.00 + 0.15×0.48 "
            f"+ 0.10×0.58 + 0.15×0.73 + 0.10×1.00 = {P17_SCORE:.4f}"
        ),
        "metrics": {m.key: m.to_dict() for m in METRICS_P17},
        "score_progression": [
            {
                "version": "P1",
                "score": round(P1_SCORE, 4),
                "classification": ScoreClassification.from_score(P1_SCORE).value,
                "key_event": "Initial reality replay evaluation",
            },
            {
                "version": "P1.5",
                "score": round(P15_SCORE, 4),
                "classification": ScoreClassification.from_score(P15_SCORE).value,
                "key_event": "Repaired false_strategy_resistance (0.65→1.00) and verifier_consistency (0.82→1.00)",
            },
            {
                "version": "P1.6",
                "score": round(P16_SCORE, 4),
                "classification": ScoreClassification.from_score(P16_SCORE).value,
                "key_event": "Upgraded precursor (0.35→0.58) and circadian (0.52→0.62) via telemetry backfill (includes interpolation)",
            },
            {
                "version": "P1.7",
                "score": round(P17_SCORE, 4),
                "classification": P17_CLASSIFICATION.value,
                "key_event": "Real-data-only revalidation: precursor (0.58→0.48) and circadian (0.62→0.58) revised downward; salience (0.72→0.73) marginal improvement",
            },
        ],
        "p17_honest_assessment": (
            "P1.7 is an HONEST CORRECTION to P1.6. By excluding interpolated data, "
            "precursor detection drops from 0.58 to 0.48 and circadian adaptation drops "
            "from 0.62 to 0.58. This reveals that P1.6's gains were partially inflated by "
            "interpolation. The real improvement from P1 (0.6645) to P1.7 (0.7795) is "
            f"+{P17_SCORE - P1_SCORE:.4f}, reflecting genuine progress from daemon "
            "deployment, enforcement modules, and real data accumulation."
        ),
    }


def generate_comparison_table() -> str:
    lines = [
        "=" * 88,
        "REALITY REPLAY SCORE — P1 → P1.5 → P1.6 → P1.7 COMPARISON",
        "=" * 88,
        "",
    ]

    header = (
        f"{'Metric':<35} {'Wt':>4} {'P1':>7} {'P1.5':>7} "
        f"{'P1.6':>7} {'P1.7':>7} {'Status':>15}"
    )
    lines.append(header)
    lines.append("-" * 88)

    for m in METRICS_P17:
        lines.append(
            f"  {m.name:<33} {m.weight:>4.2f} {m.p1_value:>7.4f} "
            f"{m.p15_value:>7.4f} {m.p16_value:>7.4f} {m.p17_value:>7.4f} "
            f"{m.p17_status:>15}"
        )

    lines.append("-" * 88)
    lines.append(
        f"  {'COMPOSITE SCORE':<33} {'1.00':>4} {P1_SCORE:>7.4f} "
        f"{P15_SCORE:>7.4f} {P16_SCORE:>7.4f} {P17_SCORE:>7.4f}"
    )

    p1_cls = ScoreClassification.from_score(P1_SCORE).value
    p15_cls = ScoreClassification.from_score(P15_SCORE).value
    p16_cls = ScoreClassification.from_score(P16_SCORE).value
    lines.append(
        f"  {'CLASSIFICATION':<33} {'':>4} {p1_cls:>7} "
        f"{p15_cls:>7} {P16_SCORE:>7.4f} {P17_CLASSIFICATION.value:>7}"
    )

    lines.append("")
    lines.append(f"  P1  → P1.5 delta:   +{P15_SCORE - P1_SCORE:.4f}")
    lines.append(f"  P1.5 → P1.6 delta:  +{P16_SCORE - P15_SCORE:.4f}")
    lines.append(f"  P1.6 → P1.7 delta:  {P17_SCORE - P16_SCORE:+.4f}")
    lines.append(f"  P1  → P1.7 total:   +{P17_SCORE - P1_SCORE:.4f}")
    lines.append("")
    lines.append("=" * 88)
    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_comparison_table())
    print()
    result = compute_full_result()
    print(json.dumps(result, indent=2))
