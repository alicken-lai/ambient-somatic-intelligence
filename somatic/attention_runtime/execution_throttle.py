"""
Adaptive Execution Throttle — Stress-based execution throttling.

Adjusts system parallelism and task scheduling based on stress level:

  Stress < 0.3:   NO_THROTTLE    — full parallelism
  Stress 0.3-0.6: MILD_THROTTLE  — reduce parallelism by 25%
  Stress 0.6-0.8: MODERATE_THROTTLE — reduce by 50%, delay non-critical
  Stress > 0.8:   HEAVY_THROTTLE — reduce by 75%, critical tasks only

SAFETY: The throttle may prioritize, delay, throttle, and escalate.
It may NOT autonomously alter protected systems, bypass governance,
or self-modify its own execution policy.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any

logger = logging.getLogger(__name__)


class ThrottleLevel(IntEnum):
    """Throttle severity levels."""
    NO_THROTTLE = 0
    MILD = 1
    MODERATE = 2
    HEAVY = 3


THROTTLE_CONFIG = {
    ThrottleLevel.NO_THROTTLE: {
        "parallelism_factor": 1.0,
        "delay_non_critical": False,
        "critical_only": False,
        "description": "No throttling — full parallelism",
    },
    ThrottleLevel.MILD: {
        "parallelism_factor": 0.75,
        "delay_non_critical": False,
        "critical_only": False,
        "description": "Mild throttle — 25% parallelism reduction",
    },
    ThrottleLevel.MODERATE: {
        "parallelism_factor": 0.50,
        "delay_non_critical": True,
        "critical_only": False,
        "description": "Moderate throttle — 50% reduction, non-critical tasks delayed",
    },
    ThrottleLevel.HEAVY: {
        "parallelism_factor": 0.25,
        "delay_non_critical": True,
        "critical_only": True,
        "description": "Heavy throttle — 75% reduction, critical tasks only",
    },
}


@dataclass
class ThrottleAction:
    """A throttle decision for a specific evaluation."""
    level: ThrottleLevel
    parallelism_factor: float
    delay_non_critical: bool
    critical_only: bool
    reason: str
    stress_level: float
    current_load: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level.name,
            "parallelism_factor": self.parallelism_factor,
            "delay_non_critical": self.delay_non_critical,
            "critical_only": self.critical_only,
            "reason": self.reason,
            "stress_level": round(self.stress_level, 4),
            "current_load": round(self.current_load, 4),
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
        }


@dataclass
class ThrottleState:
    """Current throttle state snapshot."""
    level: ThrottleLevel
    parallelism_factor: float
    delayed_tasks: int
    reason: str
    since: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level.name,
            "parallelism_factor": self.parallelism_factor,
            "delayed_tasks": self.delayed_tasks,
            "reason": self.reason,
            "since": datetime.fromtimestamp(
                self.since, tz=timezone.utc
            ).isoformat(),
            "duration_seconds": round(time.time() - self.since, 1),
        }


class AdaptiveExecutionThrottle:
    """
    Evaluates system stress and load to determine throttle actions.

    SAFETY CONSTRAINTS:
      - May: prioritize, delay, throttle, escalate
      - May NOT: alter protected systems, bypass governance,
        self-modify execution policy

    Usage:
        throttle = AdaptiveExecutionThrottle()
        action = throttle.evaluate(stress_level=0.7, current_load=0.6)
        state = throttle.get_throttle_state()
    """

    def __init__(self):
        self._current_state = ThrottleState(
            level=ThrottleLevel.NO_THROTTLE,
            parallelism_factor=1.0,
            delayed_tasks=0,
            reason="Initial state — no throttling",
        )
        self._action_history: list[ThrottleAction] = []
        self._max_history = 100
        self._delayed_task_count = 0

    def evaluate(self, stress_level: float, current_load: float) -> ThrottleAction:
        """
        Evaluate stress and load to determine the appropriate throttle action.

        Args:
            stress_level: aggregate stress score 0.0-1.0
            current_load: current system load 0.0-1.0
        """
        level = self._determine_level(stress_level)
        config = THROTTLE_CONFIG[level]

        if current_load > 0.9 and level < ThrottleLevel.MODERATE:
            level = ThrottleLevel.MODERATE
            config = THROTTLE_CONFIG[level]

        reason = self._build_reason(level, stress_level, current_load)

        action = ThrottleAction(
            level=level,
            parallelism_factor=config["parallelism_factor"],
            delay_non_critical=config["delay_non_critical"],
            critical_only=config["critical_only"],
            reason=reason,
            stress_level=stress_level,
            current_load=current_load,
        )

        if config["delay_non_critical"]:
            self._delayed_task_count += 1

        old_level = self._current_state.level
        if level != old_level:
            self._current_state = ThrottleState(
                level=level,
                parallelism_factor=config["parallelism_factor"],
                delayed_tasks=self._delayed_task_count,
                reason=reason,
            )
            logger.info(
                "Throttle level changed: %s → %s (stress=%.2f, load=%.2f)",
                old_level.name, level.name, stress_level, current_load,
            )
        else:
            self._current_state.delayed_tasks = self._delayed_task_count

        self._action_history.append(action)
        if len(self._action_history) > self._max_history:
            self._action_history = self._action_history[-self._max_history:]

        return action

    def get_throttle_state(self) -> ThrottleState:
        """Get current throttle state."""
        return self._current_state

    def reset(self) -> None:
        """Reset throttle to no-throttle state."""
        self._current_state = ThrottleState(
            level=ThrottleLevel.NO_THROTTLE,
            parallelism_factor=1.0,
            delayed_tasks=0,
            reason="Throttle reset",
        )
        self._delayed_task_count = 0
        logger.info("Throttle reset to NO_THROTTLE")

    def _determine_level(self, stress: float) -> ThrottleLevel:
        """Map stress level to throttle level."""
        if stress > 0.8:
            return ThrottleLevel.HEAVY
        elif stress > 0.6:
            return ThrottleLevel.MODERATE
        elif stress > 0.3:
            return ThrottleLevel.MILD
        return ThrottleLevel.NO_THROTTLE

    @staticmethod
    def _build_reason(
        level: ThrottleLevel,
        stress: float,
        load: float,
    ) -> str:
        """Build human-readable reason for throttle decision."""
        config = THROTTLE_CONFIG[level]
        return (
            f"{config['description']} "
            f"(stress={stress:.0%}, load={load:.0%})"
        )
