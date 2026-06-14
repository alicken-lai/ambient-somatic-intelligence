"""Evidence-driven routing decisions for deliberation modes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hermes.deliberation.memory import EffectivenessRecord
from hermes.deliberation.router.routing_policies import RoutingPolicyConfig
from hermes.deliberation.triage import triage_task


@dataclass(frozen=True)
class RoutingDecision:
    recommended_mode: str
    reason: str
    confidence: float
    why_not_single: str
    why_not_light: str
    why_not_full: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommended_mode": self.recommended_mode,
            "reason": self.reason,
            "confidence": self.confidence,
            "why_not_single": self.why_not_single,
            "why_not_light": self.why_not_light,
            "why_not_full": self.why_not_full,
            "selected_mode": self.recommended_mode,
        }


class RoutingIntelligenceEngine:
    def __init__(self, policy: RoutingPolicyConfig | None = None):
        self.policy = policy or RoutingPolicyConfig()

    def recommend(
        self,
        *,
        task: str,
        task_class: str | None = None,
        historical: EffectivenessRecord | None = None,
        risk_level: str = "normal",
    ) -> RoutingDecision:
        triage = triage_task(task)
        if triage.guardian_required or risk_level == "high":
            return RoutingDecision(
                recommended_mode="guardian_required",
                reason="Guardian-triggering risk cannot be optimized away.",
                confidence=1.0,
                why_not_single="Single mode cannot satisfy Guardian-required governance.",
                why_not_light="Light mode still needs Guardian review for this task.",
                why_not_full="Full mode without Guardian is insufficient for this task.",
            )
        if historical and historical.sample_count >= self.policy.minimum_sample_threshold:
            scores = {
                "single": historical.avg_single_score,
                "light": historical.avg_light_score,
                "full": historical.avg_full_score,
            }
            best = max(scores, key=lambda mode: scores[mode])
            sorted_scores = sorted(scores.values(), reverse=True)
            margin = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else 0.0
            confidence = min(0.95, 0.5 + (margin / 20.0) + min(0.2, historical.sample_count / 100.0))
            if margin < self.policy.quality_margin:
                best = "light" if scores["light"] >= scores["single"] else "single"
                confidence = min(confidence, 0.65)
            return self._decision_from_scores(best, scores, historical.task_class, confidence)
        fallback = triage.route_mode if triage.route_mode in {"single", "light", "full"} else "light"
        return RoutingDecision(
            recommended_mode=fallback,
            reason=f"No sufficient historical ROI for {task_class or 'unknown'}; using triage fallback.",
            confidence=0.45,
            why_not_single="Single is avoided when triage indicates uncertainty, architecture, coding, or policy complexity.",
            why_not_light="Light is avoided only when task is simple or full-mode evidence is strong.",
            why_not_full="Full is avoided without evidence that extra children improve ROI.",
        )

    def _decision_from_scores(
        self,
        selected: str,
        scores: dict[str, float],
        task_class: str,
        confidence: float,
    ) -> RoutingDecision:
        return RoutingDecision(
            recommended_mode=selected,
            reason=f"Historical score evidence for {task_class} favors {selected}.",
            confidence=round(confidence, 3),
            why_not_single=_why_not("single", selected, scores),
            why_not_light=_why_not("light", selected, scores),
            why_not_full=_why_not("full", selected, scores),
        )


def _why_not(mode: str, selected: str, scores: dict[str, float]) -> str:
    if mode == selected:
        return "Selected mode."
    return f"{mode} average score {scores[mode]:.2f} is below selected {selected} score {scores[selected]:.2f}."
