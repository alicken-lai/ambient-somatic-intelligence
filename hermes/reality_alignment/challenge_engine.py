"""Reality challenge engine."""

from __future__ import annotations

from hermes.reality_alignment.reality_models import ChallengeResult, RealityObservation, RealityTarget
from hermes.reality_alignment.reality_score import compute_reality_score


class RealityChallengeEngine:
    def select_targets(self, targets: list[RealityTarget], *, limit: int = 5) -> list[RealityTarget]:
        return sorted(
            targets,
            key=lambda item: (item.trust_score, item.confidence, item.historical_quality),
            reverse=True,
        )[:limit]

    def challenge(
        self,
        targets: list[RealityTarget],
        observations: dict[str, list[RealityObservation]] | None = None,
        *,
        limit: int = 5,
    ) -> list[ChallengeResult]:
        observations = observations or {}
        results: list[ChallengeResult] = []
        for target in self.select_targets(targets, limit=limit):
            score = compute_reality_score(target, observations.get(target.target_id, []))
            passed = score["reality_score"] >= 70.0
            reason = "trusted item retained reality contact" if passed else "trusted item needs re-verification"
            results.append(
                ChallengeResult(
                    challenge_id=f"challenge:{target.target_id}",
                    target_id=target.target_id,
                    target_type=target.target_type,
                    prior_confidence=target.confidence,
                    reality_score=float(score["reality_score"]),
                    passed=passed,
                    reason=reason,
                    challenged_because="high-trust/high-confidence items must be challenged, not only weak items",
                )
            )
        return results
