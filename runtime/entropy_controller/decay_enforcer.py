"""
Decay Enforcer — Scheduled enforcement of memory decay, TTL sweeps, and file rotation.

Assesses all entropy-generating data stores and recommends (or executes)
cleanup actions:

  Memory TTL    — find expired records per layer using MemoryKernel TTL policies
  DMN rotation  — keep last N lines in memory/dmn.jsonl, archive the rest
  Log rotation  — rotate injection_logs, context_costs, audit logs by age/count
  Access counts — cap access_counts.json growth

All enforce/execute methods default to dry_run=True. The system philosophy is:
propose, measure, and bound — not auto-modify without consent.
"""

from __future__ import annotations

# v0.4.4B: DMN rotation may use GovernedMemoryWriter when ExecutionContext is supplied.
try:
    from kernel.isolation.governed_memory_writer import GovernedMemoryWriter
except ImportError:  # pragma: no cover
    GovernedMemoryWriter = None  # type: ignore[misc, assignment]

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

TTL_POLICIES: dict[str, timedelta] = {
    "scratchpad": timedelta(hours=24),
    "episodic": timedelta(days=7),
    "governance": timedelta(days=30),
    "procedural": timedelta(days=180),
    "semantic": timedelta(days=365),
}

LOG_DIRECTORIES: list[str] = [
    "observability/injection_logs",
    "observability/context_costs",
    "observability/decisions",
    "observability/evolution_audit",
    "governance/audit",
]


@dataclass
class DecayConfig:
    """Configuration for decay enforcement thresholds."""
    dmn_max_lines: int = 2000
    log_max_age_days: int = 30
    log_max_files: int = 10
    access_count_max_entries: int = 5000
    memory_ttl_check_layers: list[str] = field(
        default_factory=lambda: ["episodic", "scratchpad"]
    )


@dataclass
class DecayTarget:
    """A data store identified as needing decay or rotation."""
    target_path: str
    target_type: str
    current_size: str
    recommended_action: str
    estimated_reduction: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_path": self.target_path,
            "target_type": self.target_type,
            "current_size": self.current_size,
            "recommended_action": self.recommended_action,
            "estimated_reduction": self.estimated_reduction,
        }


@dataclass
class DecayAssessment:
    """Complete assessment of all decay targets."""
    targets: list[DecayTarget]
    total_reclaimable: str
    assessed_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "targets": [t.to_dict() for t in self.targets],
            "total_reclaimable": self.total_reclaimable,
            "assessed_at": self.assessed_at,
        }


@dataclass
class DecayResult:
    """Result of executing (or simulating) a decay action."""
    target: DecayTarget
    executed: bool
    success: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target.to_dict(),
            "executed": self.executed,
            "success": self.success,
            "detail": self.detail,
        }


class DecayEnforcer:
    """
    Assesses and enforces memory decay, TTL sweeps, and file rotation.

    Usage:
        enforcer = DecayEnforcer(Path("/path/to/ambient-os"))
        assessment = enforcer.assess()
        results = enforcer.enforce(assessment, dry_run=True)
    """

    def __init__(
        self,
        root_dir: Path,
        config: DecayConfig | None = None,
    ) -> None:
        self._root = root_dir
        self._config = config or DecayConfig()

    def assess(self) -> DecayAssessment:
        targets: list[DecayTarget] = []

        targets.extend(self._assess_memory_ttl())

        dmn_target = self._assess_dmn_rotation()
        if dmn_target:
            targets.append(dmn_target)

        targets.extend(self._assess_log_rotation())

        access_target = self._assess_access_counts()
        if access_target:
            targets.append(access_target)

        total_reclaimable = self._estimate_total_reclaimable(targets)

        assessment = DecayAssessment(
            targets=targets,
            total_reclaimable=total_reclaimable,
            assessed_at=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            "Decay assessment: %d targets, reclaimable: %s",
            len(targets), total_reclaimable,
        )
        return assessment

    def enforce(
        self,
        assessment: DecayAssessment,
        dry_run: bool = True,
    ) -> list[DecayResult]:
        results: list[DecayResult] = []

        for target in assessment.targets:
            if dry_run:
                results.append(DecayResult(
                    target=target,
                    executed=False,
                    success=True,
                    detail=f"[DRY RUN] Would execute: {target.recommended_action}",
                ))
                continue

            result = self._execute_target(target)
            results.append(result)

        executed = sum(1 for r in results if r.executed)
        logger.info(
            "Decay enforcement: %d/%d targets executed (dry_run=%s)",
            executed, len(results), dry_run,
        )
        return results

    def _assess_memory_ttl(self) -> list[DecayTarget]:
        targets: list[DecayTarget] = []
        now = datetime.now(timezone.utc)
        memory_dir = self._root / "memory"

        for layer in self._config.memory_ttl_check_layers:
            ttl = TTL_POLICIES.get(layer)
            if not ttl:
                continue

            records_file = memory_dir / layer / "records.jsonl"
            if not records_file.exists():
                continue

            total = 0
            expired = 0
            try:
                with records_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        total += 1
                        try:
                            record = json.loads(line)
                            ts_str = record.get("timestamp", "")
                            if ts_str:
                                ts = datetime.fromisoformat(
                                    ts_str.replace("Z", "+00:00")
                                )
                                if (now - ts) > ttl:
                                    expired += 1
                        except (json.JSONDecodeError, ValueError, TypeError):
                            continue
            except OSError:
                continue

            if expired > 0:
                targets.append(DecayTarget(
                    target_path=str(records_file.relative_to(self._root)),
                    target_type="memory_layer",
                    current_size=f"{total} records ({expired} expired)",
                    recommended_action=f"ttl_sweep: archive {expired} expired records (TTL={ttl})",
                    estimated_reduction=f"{expired} records",
                ))

        return targets

    def _assess_dmn_rotation(self) -> DecayTarget | None:
        dmn_path = self._root / "memory" / "dmn.jsonl"
        if not dmn_path.exists():
            return None

        try:
            with dmn_path.open("r", encoding="utf-8") as f:
                line_count = sum(1 for line in f if line.strip())
        except OSError:
            return None

        if line_count <= self._config.dmn_max_lines:
            return None

        excess = line_count - self._config.dmn_max_lines
        return DecayTarget(
            target_path="memory/dmn.jsonl",
            target_type="dmn",
            current_size=f"{line_count} lines",
            recommended_action=f"rotate: keep last {self._config.dmn_max_lines} lines, archive {excess} oldest",
            estimated_reduction=f"{excess} lines",
        )

    def _assess_log_rotation(self) -> list[DecayTarget]:
        targets: list[DecayTarget] = []
        now = datetime.now(timezone.utc)
        max_age = timedelta(days=self._config.log_max_age_days)

        for log_dir_rel in LOG_DIRECTORIES:
            log_dir = self._root / log_dir_rel
            if not log_dir.is_dir():
                continue

            jsonl_files = sorted(log_dir.glob("*.jsonl"))
            if not jsonl_files:
                continue

            old_files: list[Path] = []
            for f in jsonl_files:
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                    if (now - mtime) > max_age:
                        old_files.append(f)
                except OSError:
                    continue

            excess_count = max(0, len(jsonl_files) - self._config.log_max_files)

            actionable = max(len(old_files), excess_count)
            if actionable > 0:
                total_size = sum(f.stat().st_size for f in jsonl_files if f.exists())
                targets.append(DecayTarget(
                    target_path=log_dir_rel,
                    target_type="log_file",
                    current_size=f"{len(jsonl_files)} files, {total_size} bytes",
                    recommended_action=(
                        f"rotate: remove {len(old_files)} aged files, "
                        f"cap at {self._config.log_max_files} files"
                    ),
                    estimated_reduction=f"~{actionable} files",
                ))

        return targets

    def _assess_access_counts(self) -> DecayTarget | None:
        ac_path = self._root / "memory" / "access_counts.json"
        if not ac_path.exists():
            return None

        try:
            data = json.loads(ac_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

        entry_count = len(data) if isinstance(data, dict) else 0
        if entry_count <= self._config.access_count_max_entries:
            return None

        excess = entry_count - self._config.access_count_max_entries
        return DecayTarget(
            target_path="memory/access_counts.json",
            target_type="access_counts",
            current_size=f"{entry_count} entries",
            recommended_action=f"prune: keep top {self._config.access_count_max_entries} by count, remove {excess} lowest",
            estimated_reduction=f"{excess} entries",
        )

    def _rotate_file(self, path: Path, max_lines: int) -> DecayResult:
        target = DecayTarget(
            target_path=str(path.relative_to(self._root)),
            target_type="file_rotation",
            current_size="",
            recommended_action=f"keep last {max_lines} lines",
            estimated_reduction="",
        )

        try:
            with path.open("r", encoding="utf-8") as f:
                lines = f.readlines()

            original_count = len(lines)
            if original_count <= max_lines:
                return DecayResult(
                    target=target, executed=True, success=True,
                    detail=f"File has {original_count} lines, within limit of {max_lines}",
                )

            archive_path = path.with_suffix(
                f".archived_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.jsonl"
            )
            with archive_path.open("w", encoding="utf-8") as f:
                f.writelines(lines[:-max_lines])

            with path.open("w", encoding="utf-8") as f:
                f.writelines(lines[-max_lines:])

            archived = original_count - max_lines
            target.current_size = f"{original_count} lines"
            target.estimated_reduction = f"{archived} lines archived"

            return DecayResult(
                target=target, executed=True, success=True,
                detail=f"Rotated: {archived} lines archived to {archive_path.name}, {max_lines} kept",
            )
        except Exception as exc:
            logger.error("File rotation failed for %s: %s", path, exc)
            return DecayResult(
                target=target, executed=True, success=False,
                detail=f"Rotation failed: {exc}",
            )

    def _execute_target(self, target: DecayTarget) -> DecayResult:
        if target.target_type == "dmn":
            return self._rotate_file(
                self._root / target.target_path,
                self._config.dmn_max_lines,
            )

        if target.target_type == "memory_layer":
            return self._execute_memory_ttl(target)

        if target.target_type == "access_counts":
            return self._execute_access_count_prune(target)

        if target.target_type == "log_file":
            return self._execute_log_rotation(target)

        return DecayResult(
            target=target, executed=False, success=False,
            detail=f"No executor for target_type={target.target_type}",
        )

    def _execute_memory_ttl(self, target: DecayTarget) -> DecayResult:
        try:
            from memory.memory_kernel import MemoryKernel
            mk = MemoryKernel(memory_dir=self._root / "memory")
            result = mk.ttl_sweep(dry_run=False)
            return DecayResult(
                target=target, executed=True, success=True,
                detail=f"TTL sweep: {result.get('total_expired', 0)} records archived",
            )
        except Exception as exc:
            logger.error("Memory TTL execution failed: %s", exc)
            return DecayResult(
                target=target, executed=True, success=False,
                detail=f"TTL sweep failed: {exc}",
            )

    def _execute_access_count_prune(self, target: DecayTarget) -> DecayResult:
        ac_path = self._root / "memory" / "access_counts.json"
        try:
            data = json.loads(ac_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return DecayResult(
                    target=target, executed=True, success=False,
                    detail="access_counts.json is not a dict",
                )

            sorted_entries = sorted(data.items(), key=lambda x: x[1], reverse=True)
            pruned = dict(sorted_entries[:self._config.access_count_max_entries])
            removed = len(data) - len(pruned)

            ac_path.write_text(
                json.dumps(pruned, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return DecayResult(
                target=target, executed=True, success=True,
                detail=f"Pruned {removed} low-access entries, kept {len(pruned)}",
            )
        except Exception as exc:
            logger.error("Access count prune failed: %s", exc)
            return DecayResult(
                target=target, executed=True, success=False,
                detail=f"Prune failed: {exc}",
            )

    def _execute_log_rotation(self, target: DecayTarget) -> DecayResult:
        log_dir = self._root / target.target_path
        if not log_dir.is_dir():
            return DecayResult(
                target=target, executed=True, success=False,
                detail=f"Directory not found: {target.target_path}",
            )

        try:
            now = datetime.now(timezone.utc)
            max_age = timedelta(days=self._config.log_max_age_days)
            jsonl_files = sorted(log_dir.glob("*.jsonl"))

            removed = 0
            for f in jsonl_files:
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                    if (now - mtime) > max_age:
                        archive_dir = log_dir / "archive"
                        archive_dir.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(f), str(archive_dir / f.name))
                        removed += 1
                except OSError:
                    continue

            remaining = sorted(log_dir.glob("*.jsonl"))
            excess = len(remaining) - self._config.log_max_files
            if excess > 0:
                for f in remaining[:excess]:
                    archive_dir = log_dir / "archive"
                    archive_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(f), str(archive_dir / f.name))
                    removed += 1

            return DecayResult(
                target=target, executed=True, success=True,
                detail=f"Rotated {removed} log files from {target.target_path}",
            )
        except Exception as exc:
            logger.error("Log rotation failed for %s: %s", target.target_path, exc)
            return DecayResult(
                target=target, executed=True, success=False,
                detail=f"Log rotation failed: {exc}",
            )

    @staticmethod
    def _estimate_total_reclaimable(targets: list[DecayTarget]) -> str:
        if not targets:
            return "0 targets — system within bounds"

        descriptions = []
        for t in targets:
            descriptions.append(f"{t.target_type}: {t.estimated_reduction}")
        return f"{len(targets)} targets — {'; '.join(descriptions)}"
