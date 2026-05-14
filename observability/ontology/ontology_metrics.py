"""Ontology health metrics for Ambient OS cognitive system."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class MetricResult:
    """Single metric measurement result."""

    name: str
    value: float  # 0.0-1.0 normalized
    raw_value: float  # original value before normalization
    weight: float  # contribution to overall score
    description: str
    measured_at: datetime


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


class OntologyMetrics:
    """Collects and computes ontology health metrics.

    Each ``measure_*`` method returns a :class:`MetricResult` whose
    ``value`` is normalised to *[0.0, 1.0]*.
    """

    def measure_instinct_formation_rate(
        self,
        l1_count: int,
        l2_count: int,
        expected_rate: float = 0.15,
    ) -> MetricResult:
        """What fraction of L1 episodes become L2 instincts?

        Healthy range: 5–25%.  Too low means the system is not learning;
        too high means it may be over-fitting.  Score is 1.0 inside the
        band and decays linearly outside it.
        """
        if l1_count <= 0:
            rate = 0.0
        else:
            rate = l2_count / l1_count

        lo, hi = 0.05, 0.25
        if lo <= rate <= hi:
            score = 1.0
        elif rate < lo:
            score = _clamp01(rate / lo) if lo > 0 else 0.0
        else:
            score = _clamp01(1.0 - (rate - hi) / (1.0 - hi)) if hi < 1.0 else 0.0

        return MetricResult(
            name="instinct_formation_rate",
            value=_clamp01(score),
            raw_value=rate,
            weight=0.0,
            description=(
                f"L1→L2 formation rate {rate:.2%} "
                f"(healthy: {lo:.0%}–{hi:.0%})"
            ),
            measured_at=_utc_now(),
        )

    def measure_promotion_precision(
        self,
        promoted_count: int,
        total_candidates: int,
        successful_promotions: int,
    ) -> MetricResult:
        """Of promoted entries, how many were actually useful?

        Score = successful_promotions / promoted_count (when > 0).
        """
        if promoted_count <= 0:
            raw = 0.0
            score = 0.0
        else:
            raw = successful_promotions / promoted_count
            score = _clamp01(raw)

        return MetricResult(
            name="promotion_precision",
            value=score,
            raw_value=raw,
            weight=0.0,
            description=(
                f"{successful_promotions}/{promoted_count} promotions successful"
            ),
            measured_at=_utc_now(),
        )

    def measure_decay_correctness(
        self,
        decayed_entries: list[float],
        contradiction_entries: list[float],
    ) -> MetricResult:
        """Do contradicted entries decay faster than non-contradicted ones?

        *decayed_entries*: confidence values of entries that decayed normally.
        *contradiction_entries*: confidence values of entries that were
        contradicted.

        Score is 1.0 when the average contradicted confidence is strictly
        lower than the average normal confidence.  Falls off linearly when
        the gap shrinks or inverts.
        """
        if not decayed_entries or not contradiction_entries:
            return MetricResult(
                name="decay_correctness",
                value=1.0 if not contradiction_entries else 0.0,
                raw_value=0.0,
                weight=0.0,
                description="Insufficient data for decay correctness",
                measured_at=_utc_now(),
            )

        avg_normal = sum(decayed_entries) / len(decayed_entries)
        avg_contra = sum(contradiction_entries) / len(contradiction_entries)

        if avg_normal <= 0:
            score = 1.0 if avg_contra <= avg_normal else 0.0
        else:
            gap = (avg_normal - avg_contra) / avg_normal
            score = _clamp01(gap)

        return MetricResult(
            name="decay_correctness",
            value=score,
            raw_value=avg_contra,
            weight=0.0,
            description=(
                f"Avg normal conf={avg_normal:.3f}, "
                f"avg contradicted conf={avg_contra:.3f}"
            ),
            measured_at=_utc_now(),
        )

    def measure_verifier_integrity(
        self,
        total_verifications: int,
        self_certifications_blocked: int,
        independent_verifications: int,
    ) -> MetricResult:
        """Are self-certifications properly blocked?

        Score = blocked / (blocked + leaked) where leaked =
        total_verifications − independent_verifications − blocked.
        Perfect score when *all* attempted self-certs were blocked.
        """
        attempted_self_certs = self_certifications_blocked + max(
            0,
            total_verifications - independent_verifications - self_certifications_blocked,
        )
        if attempted_self_certs <= 0:
            score = 1.0
            raw = 0.0
        else:
            raw = self_certifications_blocked / attempted_self_certs
            score = _clamp01(raw)

        return MetricResult(
            name="verifier_integrity",
            value=score,
            raw_value=raw,
            weight=0.0,
            description=(
                f"{self_certifications_blocked} self-certs blocked out of "
                f"{attempted_self_certs} attempts"
            ),
            measured_at=_utc_now(),
        )

    def measure_false_positive_resistance(
        self,
        noise_episodes: int,
        false_promotions: int,
    ) -> MetricResult:
        """How well does the system reject noise?

        Score = 1.0 − (false_promotions / noise_episodes).
        """
        if noise_episodes <= 0:
            score = 1.0
            raw = 0.0
        else:
            raw = false_promotions / noise_episodes
            score = _clamp01(1.0 - raw)

        return MetricResult(
            name="false_positive_resistance",
            value=score,
            raw_value=raw,
            weight=0.0,
            description=(
                f"{false_promotions} false promotions from "
                f"{noise_episodes} noise episodes"
            ),
            measured_at=_utc_now(),
        )

    def measure_strategic_emergence(
        self,
        l3_count: int,
        l4_count: int,
        l4_with_governance: int,
    ) -> MetricResult:
        """Do strategic rules emerge properly with governance?

        Score is based on two signals:
        1. L4 entries actually exist (0.4 weight).
        2. All L4 entries have governance approval (0.6 weight).
        """
        existence_score = 1.0 if l4_count > 0 else 0.0
        if l4_count > 0:
            governance_score = _clamp01(l4_with_governance / l4_count)
        else:
            governance_score = 1.0

        score = _clamp01(existence_score * 0.4 + governance_score * 0.6)

        return MetricResult(
            name="strategic_emergence",
            value=score,
            raw_value=l4_with_governance / l4_count if l4_count > 0 else 0.0,
            weight=0.0,
            description=(
                f"L4 count={l4_count}, governed={l4_with_governance}, "
                f"L3 count={l3_count}"
            ),
            measured_at=_utc_now(),
        )

    def measure_confidence_calibration(
        self,
        confidence_updates: list[dict],
    ) -> MetricResult:
        """Is confidence well-calibrated?

        Each update dict should have keys ``reason`` (str) and ``delta``
        (float, new − previous).  Successes should increase confidence
        and failures/contradictions should decrease it.  Score = fraction
        of updates that follow the expected direction.
        """
        if not confidence_updates:
            return MetricResult(
                name="confidence_calibration",
                value=1.0,
                raw_value=0.0,
                weight=0.0,
                description="No confidence updates to evaluate",
                measured_at=_utc_now(),
            )

        correct = 0
        for upd in confidence_updates:
            reason = upd.get("reason", "")
            delta = upd.get("delta", 0.0)
            if reason in ("reuse_success", "validation") and delta >= 0:
                correct += 1
            elif reason in ("reuse_failure", "contradiction", "decay") and delta <= 0:
                correct += 1

        raw = correct / len(confidence_updates)
        return MetricResult(
            name="confidence_calibration",
            value=_clamp01(raw),
            raw_value=raw,
            weight=0.0,
            description=(
                f"{correct}/{len(confidence_updates)} updates follow "
                f"expected direction"
            ),
            measured_at=_utc_now(),
        )
