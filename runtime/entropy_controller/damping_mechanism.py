"""
Damping Mechanism — Automatic damping actions triggered by entropy thresholds.

Evaluates an EntropyScore and proposes corrective actions to reduce system
complexity. By default all actions are dry-run — the mechanism PROPOSES but
does not auto-execute. Safety first.

Action types:
  ttl_sweep         — trigger MemoryKernel.ttl_sweep() for expired records
  file_rotation     — rotate oversized JSONL files, archiving old entries
  listener_cleanup  — propose listener deregistration (requires runtime)
  compression       — recommend context compression level increase
  decay_enforcement — force decay scoring pass on stale records
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.entropy_controller.entropy_scorer import DimensionScore, EntropyScore

logger = logging.getLogger(__name__)


@dataclass
class DampingConfig:
    """Thresholds and behavior for damping decisions."""
    memory_threshold: float = 0.6
    data_file_threshold: float = 0.7
    listener_threshold: float = 0.6
    auto_execute: bool = False
    dry_run_default: bool = True


@dataclass
class DampingAction:
    """A proposed damping action to reduce entropy."""
    target: str
    action_type: str
    description: str
    severity: str
    estimated_reduction: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "action_type": self.action_type,
            "description": self.description,
            "severity": self.severity,
            "estimated_reduction": self.estimated_reduction,
        }


@dataclass
class DampingResult:
    """Result of executing (or simulating) a damping action."""
    action: DampingAction
    executed: bool
    success: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.to_dict(),
            "executed": self.executed,
            "success": self.success,
            "detail": self.detail,
        }


class DampingMechanism:
    """
    Evaluates entropy scores and proposes corrective damping actions.

    Usage:
        damper = DampingMechanism(root_dir)
        actions = damper.evaluate(entropy_score)
        results = damper.execute(actions, dry_run=True)
    """

    def __init__(
        self,
        root_dir: Path,
        config: DampingConfig | None = None,
    ) -> None:
        self._root = root_dir
        self._config = config or DampingConfig()

    def evaluate(self, score: EntropyScore) -> list[DampingAction]:
        actions: list[DampingAction] = []
        dim_map = {d.name: d for d in score.dimensions}

        memory_dim = dim_map.get("memory_growth")
        if memory_dim:
            action = self._damp_memory_growth(memory_dim)
            if action:
                actions.append(action)

        data_dim = dim_map.get("data_file_growth")
        if data_dim:
            action = self._damp_data_files(data_dim)
            if action:
                actions.append(action)

        listener_dim = dim_map.get("listener_accumulation")
        if listener_dim:
            action = self._damp_listeners(listener_dim)
            if action:
                actions.append(action)

        if score.level == "critical":
            actions.append(DampingAction(
                target="system",
                action_type="decay_enforcement",
                description="Critical entropy — force full decay pass across all memory layers",
                severity="critical",
                estimated_reduction="10-30% record reduction via TTL + decay",
            ))

        if score.level in ("high", "critical"):
            context_dim = dim_map.get("context_inflation")
            if context_dim and context_dim.value > 0.3:
                actions.append(DampingAction(
                    target="context_assembly",
                    action_type="compression",
                    description="Elevated context inflation — recommend increased compression ratio",
                    severity="high" if score.level == "critical" else "medium",
                    estimated_reduction="15-25% token reduction via aggressive compression",
                ))

        logger.info(
            "Damping evaluation: %d actions proposed for entropy level %s (%.3f)",
            len(actions), score.level, score.composite,
        )
        return actions

    def execute(
        self,
        actions: list[DampingAction],
        dry_run: bool = True,
    ) -> list[DampingResult]:
        if dry_run is None:
            dry_run = self._config.dry_run_default

        results: list[DampingResult] = []
        for action in actions:
            if dry_run or not self._config.auto_execute:
                results.append(DampingResult(
                    action=action,
                    executed=False,
                    success=True,
                    detail=f"[DRY RUN] Would execute: {action.action_type} on {action.target}",
                ))
                continue

            result = self._execute_action(action)
            results.append(result)

        executed_count = sum(1 for r in results if r.executed)
        logger.info(
            "Damping execution: %d/%d actions executed (dry_run=%s)",
            executed_count, len(results), dry_run,
        )
        return results

    def _damp_memory_growth(self, dim: DimensionScore) -> DampingAction | None:
        if dim.value <= self._config.memory_threshold:
            return None

        severity = "critical" if dim.value > 0.8 else "high" if dim.value > 0.6 else "medium"
        return DampingAction(
            target="memory_layers",
            action_type="ttl_sweep",
            description=f"Memory growth at {dim.value:.0%} — trigger TTL sweep for expired records",
            severity=severity,
            estimated_reduction="5-20% depending on expired record count",
        )

    def _damp_data_files(self, dim: DimensionScore) -> DampingAction | None:
        if dim.value <= self._config.data_file_threshold:
            return None

        severity = "critical" if dim.value > 0.8 else "high"
        return DampingAction(
            target="data_files",
            action_type="file_rotation",
            description=f"Data file growth at {dim.value:.0%} — rotate oversized JSONL files",
            severity=severity,
            estimated_reduction="30-50% via archiving old entries",
        )

    def _damp_listeners(self, dim: DimensionScore) -> DampingAction | None:
        if dim.value <= self._config.listener_threshold:
            return None

        return DampingAction(
            target="listener_registry",
            action_type="listener_cleanup",
            description=f"Listener accumulation at {dim.value:.0%} — deregister stale listeners",
            severity="high",
            estimated_reduction="depends on duplicate listener count",
        )

    def _execute_action(self, action: DampingAction) -> DampingResult:
        if action.action_type == "ttl_sweep":
            return self._execute_ttl_sweep(action)
        if action.action_type == "file_rotation":
            return self._execute_file_rotation(action)
        return DampingResult(
            action=action,
            executed=False,
            success=False,
            detail=f"No executor implemented for action_type={action.action_type}",
        )

    def _execute_ttl_sweep(self, action: DampingAction) -> DampingResult:
        try:
            from memory.memory_kernel import MemoryKernel
            mk = MemoryKernel(memory_dir=self._root / "memory")
            result = mk.ttl_sweep(dry_run=False)
            return DampingResult(
                action=action,
                executed=True,
                success=True,
                detail=f"TTL sweep completed: {result.get('total_expired', 0)} records expired",
            )
        except Exception as exc:
            logger.error("TTL sweep failed: %s", exc)
            return DampingResult(
                action=action,
                executed=True,
                success=False,
                detail=f"TTL sweep failed: {exc}",
            )

    def _execute_file_rotation(self, action: DampingAction) -> DampingResult:
        try:
            from runtime.entropy_controller.decay_enforcer import DecayEnforcer
            enforcer = DecayEnforcer(self._root)
            assessment = enforcer.assess()
            log_targets = [t for t in assessment.targets if t.target_type in ("dmn", "log_file")]
            if not log_targets:
                return DampingResult(
                    action=action, executed=True, success=True,
                    detail="No files require rotation at this time",
                )
            results = enforcer.enforce(assessment, dry_run=False)
            rotated = sum(1 for r in results if r.success)
            return DampingResult(
                action=action, executed=True, success=True,
                detail=f"Rotated {rotated}/{len(log_targets)} files",
            )
        except Exception as exc:
            logger.error("File rotation failed: %s", exc)
            return DampingResult(
                action=action, executed=True, success=False,
                detail=f"File rotation failed: {exc}",
            )
