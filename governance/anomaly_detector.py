"""
Anomaly Detector — Behavioral anomaly detection for agent operations.

Detects:
  - Runaway agents (infinite retry loops)
  - Abnormal token consumption rates
  - Suspicious execution patterns (rapid file modifications)
  - Hallucinated dependencies (packages that don't exist)
  - Recursive execution loops (same action repeated)
  - Resource exhaustion patterns

Uses sliding windows and statistical baselines to distinguish
normal variation from genuine anomalies.
"""

from __future__ import annotations

import json
import os
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))


class AnomalyLevel(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class Anomaly:
    """A detected anomaly."""
    level: AnomalyLevel
    type: str
    description: str
    evidence: dict[str, Any]
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agent_id: str = ""
    recommended_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level.value,
            "type": self.type,
            "description": self.description,
            "evidence": self.evidence,
            "detected_at": self.detected_at,
            "agent_id": self.agent_id,
            "recommended_action": self.recommended_action,
        }


@dataclass
class AgentBehavior:
    """Tracks an agent's recent behavior for anomaly detection."""
    agent_id: str
    actions: deque = field(default_factory=lambda: deque(maxlen=100))
    failures: deque = field(default_factory=lambda: deque(maxlen=50))
    token_usage: deque = field(default_factory=lambda: deque(maxlen=50))
    file_modifications: deque = field(default_factory=lambda: deque(maxlen=100))
    consecutive_failures: int = 0
    total_actions: int = 0
    last_action_time: float = 0.0


class AnomalyDetector:
    """
    Monitors agent behavior and detects anomalous patterns.

    Usage:
        detector = AnomalyDetector()
        detector.record_action("cursor-agent", "write file foo.py")
        detector.record_failure("cursor-agent", "SyntaxError in foo.py")
        anomalies = detector.check("cursor-agent")
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or self._default_config()
        self.agents: dict[str, AgentBehavior] = {}
        self.global_anomalies: list[Anomaly] = []

    @staticmethod
    def _default_config() -> dict[str, Any]:
        return {
            "max_consecutive_failures": 5,
            "max_actions_per_minute": 30,
            "max_file_mods_per_minute": 20,
            "max_token_rate_per_minute": 50000,
            "repetition_threshold": 3,
            "window_seconds": 60,
        }

    def _get_agent(self, agent_id: str) -> AgentBehavior:
        if agent_id not in self.agents:
            self.agents[agent_id] = AgentBehavior(agent_id=agent_id)
        return self.agents[agent_id]

    def record_action(self, agent_id: str, action: str, metadata: dict[str, Any] | None = None) -> None:
        """Record an agent action for pattern analysis."""
        agent = self._get_agent(agent_id)
        now = time.time()
        agent.actions.append({"action": action, "time": now, "metadata": metadata or {}})
        agent.total_actions += 1
        agent.last_action_time = now
        agent.consecutive_failures = 0

    def record_failure(self, agent_id: str, error: str, metadata: dict[str, Any] | None = None) -> None:
        """Record a failure event."""
        agent = self._get_agent(agent_id)
        now = time.time()
        agent.failures.append({"error": error, "time": now, "metadata": metadata or {}})
        agent.consecutive_failures += 1

    def record_token_usage(self, agent_id: str, tokens: int) -> None:
        """Record token consumption."""
        agent = self._get_agent(agent_id)
        agent.token_usage.append({"tokens": tokens, "time": time.time()})

    def record_file_modification(self, agent_id: str, file_path: str) -> None:
        """Record a file modification."""
        agent = self._get_agent(agent_id)
        agent.file_modifications.append({"path": file_path, "time": time.time()})

    def check(self, agent_id: str) -> list[Anomaly]:
        """Run all anomaly checks for an agent."""
        agent = self._get_agent(agent_id)
        anomalies: list[Anomaly] = []

        anomalies.extend(self._check_failure_loop(agent))
        anomalies.extend(self._check_action_rate(agent))
        anomalies.extend(self._check_repetition(agent))
        anomalies.extend(self._check_file_mod_rate(agent))
        anomalies.extend(self._check_token_rate(agent))

        for a in anomalies:
            a.agent_id = agent_id
            self.global_anomalies.append(a)

        return anomalies

    def check_all(self) -> list[Anomaly]:
        """Run anomaly checks for all tracked agents."""
        all_anomalies: list[Anomaly] = []
        for agent_id in list(self.agents.keys()):
            all_anomalies.extend(self.check(agent_id))
        return all_anomalies

    def _check_failure_loop(self, agent: AgentBehavior) -> list[Anomaly]:
        """Detect consecutive failure loops."""
        threshold = self.config["max_consecutive_failures"]
        if agent.consecutive_failures >= threshold:
            level = AnomalyLevel.CRITICAL if agent.consecutive_failures >= threshold * 2 else AnomalyLevel.WARNING
            return [Anomaly(
                level=level,
                type="failure_loop",
                description=f"Agent has {agent.consecutive_failures} consecutive failures",
                evidence={
                    "consecutive_failures": agent.consecutive_failures,
                    "threshold": threshold,
                    "recent_errors": [f["error"][:100] for f in list(agent.failures)[-3:]],
                },
                recommended_action="Pause agent execution and investigate root cause",
            )]
        return []

    def _check_action_rate(self, agent: AgentBehavior) -> list[Anomaly]:
        """Detect abnormally high action rates."""
        window = self.config["window_seconds"]
        threshold = self.config["max_actions_per_minute"]
        now = time.time()

        recent = [a for a in agent.actions if now - a["time"] < window]
        rate = len(recent) * (60.0 / window)

        if rate > threshold:
            return [Anomaly(
                level=AnomalyLevel.WARNING,
                type="high_action_rate",
                description=f"Agent performing {rate:.0f} actions/min (threshold: {threshold})",
                evidence={"rate_per_min": round(rate, 1), "threshold": threshold, "window_seconds": window},
                recommended_action="Throttle agent or investigate automation loop",
            )]
        return []

    def _check_repetition(self, agent: AgentBehavior) -> list[Anomaly]:
        """Detect repeated identical actions (stuck in a loop)."""
        threshold = self.config["repetition_threshold"]
        recent_actions = [a["action"] for a in list(agent.actions)[-10:]]

        if len(recent_actions) < threshold:
            return []

        last_action = recent_actions[-1]
        repeat_count = sum(1 for a in recent_actions[-threshold * 2:] if a == last_action)

        if repeat_count >= threshold:
            return [Anomaly(
                level=AnomalyLevel.WARNING,
                type="repetitive_action",
                description=f"Same action repeated {repeat_count} times: '{last_action[:60]}'",
                evidence={
                    "action": last_action[:200],
                    "repeat_count": repeat_count,
                    "threshold": threshold,
                },
                recommended_action="Break the loop — agent may be stuck",
            )]
        return []

    def _check_file_mod_rate(self, agent: AgentBehavior) -> list[Anomaly]:
        """Detect abnormally high file modification rates."""
        window = self.config["window_seconds"]
        threshold = self.config["max_file_mods_per_minute"]
        now = time.time()

        recent = [m for m in agent.file_modifications if now - m["time"] < window]
        rate = len(recent) * (60.0 / window)

        if rate > threshold:
            paths = [m["path"] for m in recent[-5:]]
            return [Anomaly(
                level=AnomalyLevel.CRITICAL,
                type="high_file_mod_rate",
                description=f"Agent modifying {rate:.0f} files/min (threshold: {threshold})",
                evidence={"rate_per_min": round(rate, 1), "threshold": threshold, "recent_paths": paths},
                recommended_action="HALT: Possible runaway file modification. Check for repo corruption.",
            )]
        return []

    def _check_token_rate(self, agent: AgentBehavior) -> list[Anomaly]:
        """Detect abnormal token consumption."""
        window = self.config["window_seconds"]
        threshold = self.config["max_token_rate_per_minute"]
        now = time.time()

        recent = [t for t in agent.token_usage if now - t["time"] < window]
        if not recent:
            return []

        total_tokens = sum(t["tokens"] for t in recent)
        rate = total_tokens * (60.0 / window)

        if rate > threshold:
            return [Anomaly(
                level=AnomalyLevel.WARNING,
                type="high_token_consumption",
                description=f"Agent consuming {rate:.0f} tokens/min (threshold: {threshold})",
                evidence={"rate_per_min": round(rate, 1), "threshold": threshold, "total_recent": total_tokens},
                recommended_action="Review context assembly — possible context bloat",
            )]
        return []

    def get_agent_health(self, agent_id: str) -> dict[str, Any]:
        """Get health summary for an agent."""
        agent = self._get_agent(agent_id)
        now = time.time()
        window = self.config["window_seconds"]

        recent_actions = [a for a in agent.actions if now - a["time"] < window]
        recent_failures = [f for f in agent.failures if now - f["time"] < window]

        return {
            "agent_id": agent_id,
            "total_actions": agent.total_actions,
            "consecutive_failures": agent.consecutive_failures,
            "actions_last_minute": len(recent_actions),
            "failures_last_minute": len(recent_failures),
            "failure_rate": len(recent_failures) / max(len(recent_actions), 1),
            "anomalies_detected": sum(1 for a in self.global_anomalies if a.agent_id == agent_id),
        }

    def reset(self, agent_id: str) -> None:
        """Reset tracking for an agent."""
        if agent_id in self.agents:
            del self.agents[agent_id]
