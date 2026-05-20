"""Aggregate reality alignment observability for governor attachment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.reality.provenance_truth_exchange import ProvenanceTruthExchange
from governance.reality.reality_alignment import RealityAlignment
from governance.reality.reality_integrity_monitor import RealityIntegrityMonitor
from governance.reality.replay_alignment import ReplayAlignment
from governance.reality.truth_conflict_analysis import TruthConflictAnalysis


@dataclass
class RealityAlignmentObservability:
    """Read-only reality snapshot — never mutates governance acceptance."""

    advisory_only: bool = True
    alignment_ok: bool = True
    divergence_bounded: bool = True
    contamination_free: bool = True
    override_free: bool = True
    provenance_exchange_valid: bool = True
    replay_aligned: bool = True
    conflict_resolvable: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "advisory_only": self.advisory_only,
            "alignment_ok": self.alignment_ok,
            "divergence_bounded": self.divergence_bounded,
            "contamination_free": self.contamination_free,
            "override_free": self.override_free,
            "provenance_exchange_valid": self.provenance_exchange_valid,
            "replay_aligned": self.replay_aligned,
            "conflict_resolvable": self.conflict_resolvable,
            "issues": list(self.issues),
            "disclaimer": "reality_alignment_observational_only",
        }


def observe_reality_alignment(
    text: str,
    *,
    left_runtime: str = "ambient",
    right_runtime: str = "foreign",
    scope: str = "advisory",
    provenance_payload: dict[str, Any] | None = None,
    replay_hint: float = 0.0,
) -> RealityAlignmentObservability:
    alignment = RealityAlignment()
    verdict = alignment.evaluate(
        text,
        left_runtime=left_runtime,
        right_runtime=right_runtime,
        scope=scope,
    )
    pe = ProvenanceTruthExchange().validate(provenance_payload, sovereign_id=right_runtime)
    replay = ReplayAlignment().evaluate(text, replay_hint=replay_hint)
    conflict = TruthConflictAnalysis().analyze(text)
    integrity = RealityIntegrityMonitor().check(text)

    issues = list(verdict.reasons)
    if not pe.exchange_valid:
        issues.extend(pe.issues)
    if not replay.aligned:
        issues.extend(replay.issues)
    if not integrity.integrity_ok:
        issues.extend(integrity.issues)

    return RealityAlignmentObservability(
        advisory_only=True,
        alignment_ok=verdict.aligned,
        divergence_bounded=verdict.divergence_bounded,
        contamination_free=verdict.contamination_free,
        override_free=verdict.override_free,
        provenance_exchange_valid=pe.exchange_valid,
        replay_aligned=replay.aligned,
        conflict_resolvable=conflict.resolvable_without_merge,
        issues=issues,
    )
