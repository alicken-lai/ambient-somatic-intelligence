"""
Execution Validator — Pre-execution safety validation pipeline.

A multi-stage validation pipeline that runs BEFORE any action executes:
  Stage 1: Policy check (PolicyEngine)
  Stage 2: Anomaly check (AnomalyDetector)
  Stage 3: Resource protection (protected paths/branches)
  Stage 4: Context validation (prompt injection detection)

The validator produces a ValidationResult that either ALLOWS execution
or provides a detailed rejection with reasons and suggestions.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from governance.policy_engine import PolicyEngine, PolicyDecision, RiskLevel
from governance.anomaly_detector import AnomalyDetector, AnomalyLevel


AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))

PROTECTED_PATHS = [
    r"^/etc/",
    r"^/usr/",
    r"^/System/",
    r"^~?/\.ssh/",
    r"^~?/\.gnupg/",
    r"\.env$",
    r"credentials\.json$",
    r"private_key",
    r"id_rsa",
]

PROTECTED_BRANCHES = ["main", "master", "production", "release"]

INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+(instructions|rules|prompts)",
    r"you\s+are\s+now\s+(a|an)\s+",
    r"forget\s+(everything|all|your)\s+(instructions|rules)",
    r"system\s*:\s*you\s+are",
    r"<\s*system\s*>",
    r"\]\]\s*\[\[",
]


@dataclass
class ValidationStage:
    """Result of a single validation stage."""
    name: str
    passed: bool
    risk: RiskLevel
    details: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Complete validation pipeline result."""
    allowed: bool
    risk: RiskLevel
    action: str
    stages: list[ValidationStage]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agent_id: str = ""
    suggestions: list[str] = field(default_factory=list)

    @property
    def blocking_stage(self) -> ValidationStage | None:
        for stage in self.stages:
            if not stage.passed:
                return stage
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "risk": self.risk.name,
            "action": self.action,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "stages": [
                {"name": s.name, "passed": s.passed, "risk": s.risk.name, "details": s.details}
                for s in self.stages
            ],
            "blocking_stage": self.blocking_stage.name if self.blocking_stage else None,
            "suggestions": self.suggestions,
        }


class ExecutionValidator:
    """
    Pre-execution validation pipeline.

    Usage:
        validator = ExecutionValidator()
        result = validator.validate(
            action="rm -rf /tmp/old_data",
            agent_id="cursor-agent",
            resource="/tmp/old_data",
        )
        if not result.allowed:
            print(f"BLOCKED at stage '{result.blocking_stage.name}': {result.blocking_stage.details}")
    """

    def __init__(
        self,
        policy_engine: PolicyEngine | None = None,
        anomaly_detector: AnomalyDetector | None = None,
        protected_paths: list[str] | None = None,
        protected_branches: list[str] | None = None,
    ):
        self.policy_engine = policy_engine or PolicyEngine()
        self.anomaly_detector = anomaly_detector or AnomalyDetector()
        self.protected_paths = [re.compile(p) for p in (protected_paths or PROTECTED_PATHS)]
        self.protected_branches = protected_branches or PROTECTED_BRANCHES

    def validate(
        self,
        action: str,
        agent_id: str = "unknown",
        resource: str = "",
        scopes: list[str] | None = None,
        context: str = "",
    ) -> ValidationResult:
        """
        Run the full validation pipeline.

        Returns ValidationResult indicating whether execution should proceed.
        """
        stages: list[ValidationStage] = []
        suggestions: list[str] = []

        # Stage 1: Policy Engine
        stage1 = self._stage_policy(action, agent_id, scopes or [], resource)
        stages.append(stage1)
        if not stage1.passed:
            suggestions.append(f"Policy '{stage1.metadata.get('policy', '')}' blocks this action")

        # Stage 2: Anomaly Detection
        stage2 = self._stage_anomaly(agent_id)
        stages.append(stage2)
        if not stage2.passed:
            suggestions.append("Agent showing anomalous behavior — consider pausing")

        # Stage 3: Resource Protection
        stage3 = self._stage_resource_protection(action, resource)
        stages.append(stage3)
        if not stage3.passed:
            suggestions.append(f"Protected resource: {stage3.metadata.get('matched_pattern', '')}")

        # Stage 4: Injection Detection
        stage4 = self._stage_injection_check(action, context)
        stages.append(stage4)
        if not stage4.passed:
            suggestions.append("Possible prompt injection detected — review input carefully")

        all_passed = all(s.passed for s in stages)
        max_risk = max(s.risk for s in stages)

        return ValidationResult(
            allowed=all_passed,
            risk=max_risk,
            action=action,
            stages=stages,
            agent_id=agent_id,
            suggestions=suggestions,
        )

    def _stage_policy(
        self, action: str, agent_id: str, scopes: list[str], resource: str,
    ) -> ValidationStage:
        """Stage 1: Policy Engine evaluation."""
        decision = self.policy_engine.evaluate(
            action=action,
            agent_id=agent_id,
            scopes=scopes,
            resource=resource,
        )

        passed = decision.risk == RiskLevel.ALLOW
        return ValidationStage(
            name="policy_engine",
            passed=passed,
            risk=decision.risk,
            details=decision.reason,
            metadata={
                "policy": decision.matched_policies[0].name if decision.matched_policies else "",
                "matched_count": len(decision.matched_policies),
            },
        )

    def _stage_anomaly(self, agent_id: str) -> ValidationStage:
        """Stage 2: Anomaly detection check."""
        anomalies = self.anomaly_detector.check(agent_id)

        critical = [a for a in anomalies if a.level in (AnomalyLevel.CRITICAL, AnomalyLevel.EMERGENCY)]
        warnings = [a for a in anomalies if a.level == AnomalyLevel.WARNING]

        if critical:
            return ValidationStage(
                name="anomaly_detection",
                passed=False,
                risk=RiskLevel.BLOCK,
                details=critical[0].description,
                metadata={"anomaly_type": critical[0].type, "count": len(critical)},
            )
        elif warnings:
            return ValidationStage(
                name="anomaly_detection",
                passed=True,  # Warnings don't block, but are noted
                risk=RiskLevel.REVIEW_REQUIRED,
                details=f"{len(warnings)} warning(s): {warnings[0].description}",
                metadata={"warning_count": len(warnings)},
            )

        return ValidationStage(
            name="anomaly_detection",
            passed=True,
            risk=RiskLevel.ALLOW,
            details="No anomalies detected",
        )

    def _stage_resource_protection(self, action: str, resource: str) -> ValidationStage:
        """Stage 3: Protected resource check."""
        check_target = resource or action

        for pattern in self.protected_paths:
            if pattern.search(check_target):
                return ValidationStage(
                    name="resource_protection",
                    passed=False,
                    risk=RiskLevel.BLOCK,
                    details=f"Action targets protected resource matching: {pattern.pattern}",
                    metadata={"matched_pattern": pattern.pattern, "resource": check_target[:200]},
                )

        for branch in self.protected_branches:
            if re.search(rf"\b{branch}\b", check_target) and any(
                kw in action.lower() for kw in ("force", "delete", "reset --hard")
            ):
                return ValidationStage(
                    name="resource_protection",
                    passed=False,
                    risk=RiskLevel.BLOCK,
                    details=f"Destructive action on protected branch: {branch}",
                    metadata={"branch": branch},
                )

        return ValidationStage(
            name="resource_protection",
            passed=True,
            risk=RiskLevel.ALLOW,
            details="No protected resources affected",
        )

    def _stage_injection_check(self, action: str, context: str) -> ValidationStage:
        """Stage 4: Prompt injection detection."""
        check_text = f"{action} {context}".lower()

        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, check_text, re.IGNORECASE):
                return ValidationStage(
                    name="injection_detection",
                    passed=False,
                    risk=RiskLevel.BLOCK,
                    details=f"Potential prompt injection detected (pattern: {pattern[:40]}...)",
                    metadata={"pattern": pattern},
                )

        return ValidationStage(
            name="injection_detection",
            passed=True,
            risk=RiskLevel.ALLOW,
            details="No injection patterns detected",
        )
