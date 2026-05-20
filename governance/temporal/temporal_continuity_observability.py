"""Aggregate temporal continuity observability for governor attachment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.temporal.continuity_conflict import ContinuityConflict
from governance.temporal.replay_continuity_analysis import ReplayContinuityAnalysis
from governance.temporal.temporal_integrity_monitor import TemporalIntegrityMonitor
from governance.temporal.temporal_provenance import TemporalProvenance
from governance.temporal.temporal_continuity import TemporalContinuity


@dataclass
class TemporalContinuityObservability:
    """Read-only temporal snapshot — never mutates governance acceptance."""

    advisory_only: bool = True
    continuity_ok: bool = True
    fragmentation_bounded: bool = True
    contamination_free: bool = True
    lineage_valid: bool = True
    provenance_valid: bool = True
    replay_continuous: bool = True
    conflict_resolvable: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "advisory_only": self.advisory_only,
            "continuity_ok": self.continuity_ok,
            "fragmentation_bounded": self.fragmentation_bounded,
            "contamination_free": self.contamination_free,
            "lineage_valid": self.lineage_valid,
            "provenance_valid": self.provenance_valid,
            "replay_continuous": self.replay_continuous,
            "conflict_resolvable": self.conflict_resolvable,
            "issues": list(self.issues),
            "disclaimer": "temporal_continuity_observational_only",
        }


def observe_temporal_continuity(
    text: str,
    *,
    epoch_id: str = "current",
    runtime_id: str = "ambient",
    scope: str = "advisory",
    provenance_payload: dict[str, Any] | None = None,
    replay_hint: float = 0.0,
) -> TemporalContinuityObservability:
    continuity = TemporalContinuity()
    verdict = continuity.evaluate(
        text,
        epoch_id=epoch_id,
        runtime_id=runtime_id,
        scope=scope,
    )
    prov = TemporalProvenance().validate(provenance_payload, sovereign_id=runtime_id)
    replay = ReplayContinuityAnalysis().evaluate(text, replay_hint=replay_hint)
    conflict = ContinuityConflict().analyze(text)
    integrity = TemporalIntegrityMonitor().check(text)

    issues = list(verdict.reasons)
    if not prov.provenance_valid:
        issues.extend(prov.issues)
    if not replay.aligned:
        issues.extend(replay.issues)
    if not integrity.integrity_ok:
        issues.extend(integrity.issues)

    return TemporalContinuityObservability(
        advisory_only=True,
        continuity_ok=verdict.continuous,
        fragmentation_bounded=verdict.fragmentation_bounded,
        contamination_free=verdict.contamination_free,
        lineage_valid=verdict.lineage_valid,
        provenance_valid=prov.provenance_valid,
        replay_continuous=replay.aligned,
        conflict_resolvable=conflict.resolvable_without_sync,
        issues=issues,
    )
