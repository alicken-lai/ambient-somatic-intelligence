"""
Incident Learner — Learn from governance incidents and decisions.

Reads governance audit logs (incidents.jsonl and decisions.jsonl) to identify
patterns in policy violations, recurring blocks, and opportunities to refine
governance policies.
"""

from __future__ import annotations

import json
import logging
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class IncidentAnalysis:
    """Analysis results from governance incidents."""
    total_incidents: int
    by_type: dict[str, int]
    by_severity: dict[str, int]
    recurring_patterns: list[dict[str, Any]]
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_incidents": self.total_incidents,
            "by_type": self.by_type,
            "by_severity": self.by_severity,
            "recurring_patterns": self.recurring_patterns,
            "recommendations": self.recommendations,
        }


@dataclass
class DecisionAnalysis:
    """Analysis results from governance decisions."""
    total_decisions: int
    by_risk_level: dict[str, int]
    policies_triggered: dict[str, int]
    agents_blocked: dict[str, int]
    false_positive_estimate: float
    review_required_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_decisions": self.total_decisions,
            "by_risk_level": self.by_risk_level,
            "policies_triggered": self.policies_triggered,
            "agents_blocked": self.agents_blocked,
            "false_positive_estimate": round(self.false_positive_estimate, 3),
            "review_required_ratio": round(self.review_required_ratio, 3),
        }


@dataclass
class PolicyRecommendation:
    """A recommended policy adjustment."""
    policy_name: str
    recommendation: str
    reason: str
    confidence: float
    evidence_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_name": self.policy_name,
            "recommendation": self.recommendation,
            "reason": self.reason,
            "confidence": round(self.confidence, 3),
            "evidence_count": self.evidence_count,
        }


class IncidentLearner:
    """
    Learn from governance incidents and decisions to suggest policy improvements.

    Reads audit logs, categorizes incidents, identifies patterns, and generates
    recommendations for policy adjustments.

    Usage:
        learner = IncidentLearner()
        analysis = learner.analyze_incidents()
        decisions = learner.learn_from_decisions()
        recommendations = learner.generate_policy_recommendations()
    """

    def __init__(self, incidents_path: Path | str | None = None):
        if incidents_path is None:
            root = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
            self._incidents_path = root / "governance" / "audit" / "incidents.jsonl"
        else:
            self._incidents_path = Path(incidents_path)

        self._decisions_path = self._incidents_path.parent / "decisions.jsonl"

    def analyze_incidents(self) -> IncidentAnalysis:
        """
        Read and analyze governance incidents.

        Categorizes incidents by type and severity, identifies recurring patterns,
        and generates recommendations.
        """
        incidents = self._load_jsonl(self._incidents_path)

        if not incidents:
            logger.info("No incidents found at %s", self._incidents_path)
            return IncidentAnalysis(
                total_incidents=0,
                by_type={},
                by_severity={},
                recurring_patterns=[],
                recommendations=["No incidents recorded — baseline governance appears healthy"],
            )

        by_type: dict[str, int] = Counter()
        by_severity: dict[str, int] = Counter()
        agent_incidents: dict[str, list[dict]] = defaultdict(list)
        policy_incidents: dict[str, int] = Counter()

        for incident in incidents:
            incident_type = incident.get("type", "unknown")
            by_type[incident_type] += 1

            severity = self._infer_severity(incident)
            by_severity[severity] += 1

            agent_id = incident.get("agent_id", "unknown")
            agent_incidents[agent_id].append(incident)

            for policy in incident.get("policies", []):
                policy_incidents[policy] += 1

        recurring_patterns = self._find_recurring_patterns(incidents, agent_incidents)
        recommendations = self._generate_incident_recommendations(
            by_type, agent_incidents, policy_incidents
        )

        return IncidentAnalysis(
            total_incidents=len(incidents),
            by_type=dict(by_type),
            by_severity=dict(by_severity),
            recurring_patterns=recurring_patterns,
            recommendations=recommendations,
        )

    def learn_from_decisions(self, decisions_path: Path | str | None = None) -> DecisionAnalysis:
        """
        Analyze governance decisions to find policy effectiveness patterns.

        Identifies which policies trigger most, which agents get blocked most,
        and estimates false positive rates.
        """
        path = Path(decisions_path) if decisions_path else self._decisions_path
        decisions = self._load_jsonl(path)

        if not decisions:
            logger.info("No decisions found at %s", path)
            return DecisionAnalysis(
                total_decisions=0,
                by_risk_level={},
                policies_triggered={},
                agents_blocked={},
                false_positive_estimate=0.0,
                review_required_ratio=0.0,
            )

        by_risk: dict[str, int] = Counter()
        policies_triggered: dict[str, int] = Counter()
        agents_blocked: dict[str, int] = Counter()
        review_count = 0
        allow_count = 0

        for decision in decisions:
            risk = decision.get("risk", "UNKNOWN")
            by_risk[risk] += 1

            if risk == "ALLOW":
                allow_count += 1
            elif risk == "REVIEW_REQUIRED":
                review_count += 1

            for policy in decision.get("matched_policies", []):
                policies_triggered[policy] += 1

            if risk == "BLOCK":
                agent_id = decision.get("agent_id", "unknown")
                agents_blocked[agent_id] += 1

        total = len(decisions)
        false_positive_estimate = self._estimate_false_positives(decisions)
        review_ratio = review_count / total if total > 0 else 0.0

        return DecisionAnalysis(
            total_decisions=total,
            by_risk_level=dict(by_risk),
            policies_triggered=dict(policies_triggered),
            agents_blocked=dict(agents_blocked),
            false_positive_estimate=false_positive_estimate,
            review_required_ratio=review_ratio,
        )

    def generate_policy_recommendations(self) -> list[PolicyRecommendation]:
        """
        Generate policy adjustment recommendations based on incident patterns.

        Combines insights from incidents and decisions to suggest concrete
        policy refinements.
        """
        incident_analysis = self.analyze_incidents()
        decision_analysis = self.learn_from_decisions()
        recommendations: list[PolicyRecommendation] = []

        if decision_analysis.false_positive_estimate > 0.3:
            recommendations.append(PolicyRecommendation(
                policy_name="general",
                recommendation="Reduce false positive rate by relaxing overly broad policies",
                reason=f"Estimated false positive rate is {decision_analysis.false_positive_estimate:.1%}",
                confidence=0.7,
                evidence_count=decision_analysis.total_decisions,
            ))

        if decision_analysis.review_required_ratio > 0.4:
            recommendations.append(PolicyRecommendation(
                policy_name="review_policies",
                recommendation="Consider auto-approving low-risk REVIEW_REQUIRED actions",
                reason=f"Review ratio is {decision_analysis.review_required_ratio:.1%} — high review burden",
                confidence=0.6,
                evidence_count=decision_analysis.total_decisions,
            ))

        for agent_id, block_count in decision_analysis.agents_blocked.items():
            if block_count >= 3:
                recommendations.append(PolicyRecommendation(
                    policy_name=f"agent_permissions_{agent_id}",
                    recommendation=f"Review permissions for agent '{agent_id}' — frequently blocked",
                    reason=f"Agent blocked {block_count} times; may need scope expansion or task reassignment",
                    confidence=min(0.9, block_count / 10.0),
                    evidence_count=block_count,
                ))

        for policy, count in decision_analysis.policies_triggered.items():
            if count >= 5:
                recommendations.append(PolicyRecommendation(
                    policy_name=policy,
                    recommendation=f"Policy '{policy}' triggers very frequently — consider refinement",
                    reason=f"Triggered {count} times; may be too broad or need exception rules",
                    confidence=min(0.8, count / 15.0),
                    evidence_count=count,
                ))

        for pattern in incident_analysis.recurring_patterns:
            if pattern.get("count", 0) >= 3:
                recommendations.append(PolicyRecommendation(
                    policy_name=pattern.get("related_policy", "unknown"),
                    recommendation=f"Address recurring pattern: {pattern.get('description', 'unknown')}",
                    reason=f"Pattern recurred {pattern['count']} times across {pattern.get('agents', 0)} agents",
                    confidence=0.7,
                    evidence_count=pattern["count"],
                ))

        recommendations.sort(key=lambda r: (r.confidence, r.evidence_count), reverse=True)
        return recommendations

    def _load_jsonl(self, path: Path) -> list[dict[str, Any]]:
        """Load records from a JSONL file, gracefully handling missing files."""
        if not path.exists():
            return []
        records: list[dict[str, Any]] = []
        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except OSError as e:
            logger.warning("Failed to read %s: %s", path, e)
        return records

    def _infer_severity(self, incident: dict[str, Any]) -> str:
        """Infer incident severity from available fields."""
        action = incident.get("action", "").lower()
        incident_type = incident.get("type", "")

        if "rm -rf" in action or "drop database" in action:
            return "critical"
        if incident_type == "blocked_action" and incident.get("policies"):
            return "high"
        if incident_type == "blocked_action":
            return "medium"
        return "low"

    def _find_recurring_patterns(
        self,
        incidents: list[dict[str, Any]],
        agent_incidents: dict[str, list[dict]],
    ) -> list[dict[str, Any]]:
        """Identify recurring incident patterns."""
        patterns: list[dict[str, Any]] = []

        action_counter: dict[str, int] = Counter()
        for incident in incidents:
            action = incident.get("action", "unknown")
            action_counter[action] += 1

        for action, count in action_counter.most_common(10):
            if count >= 2:
                agents_involved = [
                    aid for aid, incs in agent_incidents.items()
                    if any(i.get("action") == action for i in incs)
                ]
                related_policies = set()
                for incident in incidents:
                    if incident.get("action") == action:
                        for p in incident.get("policies", []):
                            related_policies.add(p)

                patterns.append({
                    "description": f"Action '{action}' repeatedly blocked",
                    "count": count,
                    "agents": len(agents_involved),
                    "agents_involved": agents_involved,
                    "related_policy": next(iter(related_policies), "unknown"),
                })

        return patterns

    def _generate_incident_recommendations(
        self,
        by_type: dict[str, int],
        agent_incidents: dict[str, list[dict]],
        policy_incidents: dict[str, int],
    ) -> list[str]:
        """Generate text recommendations from incident patterns."""
        recommendations: list[str] = []

        blocked = by_type.get("blocked_action", 0)
        if blocked > 5:
            recommendations.append(
                f"High block rate ({blocked} incidents) — review if policies are too restrictive"
            )

        repeat_offenders = [
            (aid, len(incs)) for aid, incs in agent_incidents.items()
            if len(incs) >= 3
        ]
        for agent_id, count in sorted(repeat_offenders, key=lambda x: x[1], reverse=True):
            recommendations.append(
                f"Agent '{agent_id}' triggered {count} incidents — consider permission audit"
            )

        if not recommendations:
            recommendations.append("Incident rate is within expected bounds")

        return recommendations

    def _estimate_false_positives(self, decisions: list[dict[str, Any]]) -> float:
        """
        Estimate false positive rate from decision patterns.

        Heuristic: if an agent is blocked for an action but the same action
        is allowed for other agents, it may indicate a false positive.
        """
        action_outcomes: dict[str, dict[str, int]] = defaultdict(lambda: {"allow": 0, "block": 0})

        for decision in decisions:
            action = decision.get("action", "")
            risk = decision.get("risk", "")
            if risk == "ALLOW":
                action_outcomes[action]["allow"] += 1
            elif risk == "BLOCK":
                action_outcomes[action]["block"] += 1

        mixed_signals = 0
        total_blocked = 0
        for action, outcomes in action_outcomes.items():
            if outcomes["block"] > 0:
                total_blocked += outcomes["block"]
                if outcomes["allow"] > 0:
                    mixed_signals += outcomes["block"]

        if total_blocked == 0:
            return 0.0
        return mixed_signals / total_blocked
