"""Constitutional guard — evaluate BEFORE arbitration; block violations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.constitution.constitution import Constitution, load_constitution
from governance.constitution.constitutional_violation import ConstitutionalVerdict, ConstitutionalViolation
from governance.constitution.epistemic_limit import check_epistemic_limit
from governance.constitution.forecast_boundary import check_forecast_boundary
from governance.constitution.guardian_supremacy import check_guardian_supremacy
from governance.constitution.replay_boundary import check_replay_boundary
from governance.constitution.self_modification_guard import check_self_modification
_FORBIDDEN_RECURSIVE_ROUTES = frozenset({
    "governance_on_governance",
    "cognitive_self_loop",
})


@dataclass
class ConstitutionalContext:
    route_name: str = "attention_submit"
    raw_confidence: float = 0.7
    uncertainty: float = 0.35
    replay_hint: float = 0.0
    certainty_claim: bool = False
    deterministic_authority: bool = False
    guardian_bypass_attempt: bool = False
    weaken_guardian: bool = False
    replay_executes: bool = False
    replay_write: bool = False
    collapse_uncertainty: bool = False
    forecast_certainty: bool = False
    mutation_attempt: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class ConstitutionalGuard:
    """
    Frozen constitutional evaluator.

    Runs before CognitiveGovernor arbitration. Blocks violations; never mutates rules.
    """

    def __init__(self, constitution: Constitution | None = None) -> None:
        self.constitution = constitution or load_constitution(seal=True)
        if not self.constitution.sealed:
            self.constitution.seal()

    def evaluate(self, ctx: ConstitutionalContext) -> ConstitutionalVerdict:
        trace: list[str] = ["constitutional_guard"]
        violations: list[ConstitutionalViolation] = []

        checks = [
            check_guardian_supremacy(
                route_name=ctx.route_name,
                guardian_bypass_attempt=ctx.guardian_bypass_attempt,
                weaken_guardian=ctx.weaken_guardian,
            ),
            check_epistemic_limit(
                raw_confidence=ctx.raw_confidence,
                certainty_claim=ctx.certainty_claim,
                deterministic_authority=ctx.deterministic_authority,
            ),
            check_replay_boundary(
                replay_hint=ctx.replay_hint,
                replay_executes=ctx.replay_executes,
                replay_write=ctx.replay_write,
            ),
            check_forecast_boundary(
                uncertainty=ctx.uncertainty,
                collapse_uncertainty=ctx.collapse_uncertainty,
                forecast_certainty=ctx.forecast_certainty,
            ),
            check_self_modification(
                self.constitution._lock,
                metadata=ctx.metadata,
                mutation_attempt=ctx.mutation_attempt,
            ),
        ]

        if ctx.route_name in _FORBIDDEN_RECURSIVE_ROUTES:
            violations.append(
                ConstitutionalViolation(
                    rule_id="no_recursive_governance",
                    message=f"recursive_route:{ctx.route_name}",
                    severity="block",
                )
            )
            trace.append("recursive_governance_blocked")

        for v in checks:
            if v is not None:
                violations.append(v)
                trace.append(f"violation:{v.rule_id}")

        if violations:
            trace.append("constitutional_block")
            return ConstitutionalVerdict(compliant=False, violations=violations, trace=trace)

        trace.append("constitutional_ok")
        return ConstitutionalVerdict(compliant=True, violations=[], trace=trace)
