"""Civilization lineage integrity V2 — post v0.7.x-P horizon normalization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from observability.v07x_freeze.civilization_lineage_integrity_score import (
    CIVILIZATION_LINEAGE_FREEZE_THRESHOLD,
    CivilizationLineageIntegrityScore,
    evaluate_civilization_lineage_integrity,
)

CIVILIZATION_LINEAGE_FREEZE_THRESHOLD_V2 = CIVILIZATION_LINEAGE_FREEZE_THRESHOLD


@dataclass
class CivilizationLineageIntegrityScoreV2:
    """V2 wraps V1 evaluation with stabilization program metadata."""

    lineage_integrity_score: float
    mean_lineage_score: float
    min_lineage_score: float
    max_lineage_score: float
    gate_pass: bool
    gate_threshold: float = CIVILIZATION_LINEAGE_FREEZE_THRESHOLD_V2
    layers: list[dict[str, Any]] = field(default_factory=list)
    all_layer_gates_pass: bool = False
    classification: str = "restricted_civilization_lineage"
    gap_to_threshold: float = 0.0
    stabilization_program: str = "v07xp"
    horizon_fix: str = "v070_parent_retention_0.88"

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineage_integrity_score": round(self.lineage_integrity_score, 6),
            "mean_lineage_score": round(self.mean_lineage_score, 6),
            "min_lineage_score": round(self.min_lineage_score, 6),
            "max_lineage_score": round(self.max_lineage_score, 6),
            "gate_pass": self.gate_pass,
            "gate_threshold": self.gate_threshold,
            "all_layer_gates_pass": self.all_layer_gates_pass,
            "classification": self.classification,
            "gap_to_threshold": round(self.gap_to_threshold, 6),
            "layers": self.layers,
            "stabilization_program": self.stabilization_program,
            "horizon_fix": self.horizon_fix,
        }


@dataclass
class CivilizationFreezeSnapshotV2:
    report: CivilizationLineageIntegrityScoreV2
    program_version: str = "v07xp"

    def to_dict(self) -> dict[str, Any]:
        payload = self.report.to_dict()
        payload["program_version"] = self.program_version
        payload["snapshot_schema"] = "civilization_freeze_snapshot_v2"
        return payload


def evaluate_civilization_lineage_integrity_v2() -> CivilizationLineageIntegrityScoreV2:
    base: CivilizationLineageIntegrityScore = evaluate_civilization_lineage_integrity()
    return CivilizationLineageIntegrityScoreV2(
        lineage_integrity_score=base.lineage_integrity_score,
        mean_lineage_score=base.mean_lineage_score,
        min_lineage_score=base.min_lineage_score,
        max_lineage_score=base.max_lineage_score,
        gate_pass=base.gate_pass,
        gate_threshold=base.gate_threshold,
        layers=[layer.to_dict() for layer in base.layers],
        all_layer_gates_pass=base.all_layer_gates_pass,
        classification=base.classification,
        gap_to_threshold=base.gap_to_threshold,
    )
