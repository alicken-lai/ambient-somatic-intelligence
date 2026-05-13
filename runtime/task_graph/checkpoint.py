"""
Checkpoint Manager — Execution snapshots and rollback support.

Provides persistence for TaskGraph execution state:
  - Save checkpoints at each stage boundary
  - Resume from last checkpoint on failure/restart
  - Rollback to a previous checkpoint
  - Maintain checkpoint history for debugging

Checkpoints are stored as JSON files in state/checkpoints/.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.task_graph.dag import TaskGraph


AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
CHECKPOINT_DIR = AMBIENT_ROOT / "state" / "checkpoints"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Checkpoint:
    """A single checkpoint snapshot."""

    def __init__(
        self,
        checkpoint_id: str,
        graph_data: dict[str, Any],
        stage: int,
        metadata: dict[str, Any] | None = None,
    ):
        self.id = checkpoint_id
        self.graph_data = graph_data
        self.stage = stage
        self.created_at = utc_now()
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "graph_data": self.graph_data,
            "stage": self.stage,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Checkpoint":
        cp = cls(
            checkpoint_id=data["id"],
            graph_data=data["graph_data"],
            stage=data["stage"],
            metadata=data.get("metadata", {}),
        )
        cp.created_at = data.get("created_at", cp.created_at)
        return cp


class CheckpointManager:
    """
    Manages checkpoint lifecycle for TaskGraph execution.

    Usage:
        mgr = CheckpointManager()
        mgr.save(graph, stage=0)            # Save checkpoint
        graph = mgr.restore(graph_id)        # Restore from latest checkpoint
        mgr.rollback(graph_id, stage=1)      # Rollback to specific stage
    """

    def __init__(self, checkpoint_dir: Path | None = None):
        self.checkpoint_dir = checkpoint_dir or CHECKPOINT_DIR
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def _graph_dir(self, graph_id: str) -> Path:
        return self.checkpoint_dir / graph_id

    def save(
        self,
        graph: TaskGraph,
        stage: int,
        metadata: dict[str, Any] | None = None,
    ) -> Checkpoint:
        """Save a checkpoint of the current graph state."""
        graph_dir = self._graph_dir(graph.id)
        graph_dir.mkdir(parents=True, exist_ok=True)

        checkpoint_id = f"{graph.id}_stage{stage}_{datetime.now(timezone.utc).strftime('%H%M%S')}"

        cp = Checkpoint(
            checkpoint_id=checkpoint_id,
            graph_data=graph.to_dict(),
            stage=stage,
            metadata=metadata,
        )

        cp_path = graph_dir / f"stage_{stage:03d}.json"
        cp_path.write_text(
            json.dumps(cp.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        latest_path = graph_dir / "latest.json"
        latest_path.write_text(
            json.dumps(cp.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        return cp

    def restore(self, graph_id: str, stage: int | None = None) -> TaskGraph | None:
        """
        Restore a TaskGraph from checkpoint.

        If stage is None, restores from the latest checkpoint.
        """
        graph_dir = self._graph_dir(graph_id)
        if not graph_dir.exists():
            return None

        if stage is not None:
            cp_path = graph_dir / f"stage_{stage:03d}.json"
        else:
            cp_path = graph_dir / "latest.json"

        if not cp_path.exists():
            return None

        data = json.loads(cp_path.read_text(encoding="utf-8"))
        cp = Checkpoint.from_dict(data)
        return TaskGraph.from_dict(cp.graph_data)

    def rollback(self, graph_id: str, to_stage: int) -> TaskGraph | None:
        """
        Rollback to a specific stage, resetting all subsequent task states.

        Tasks completed in stages after to_stage are reset to PENDING.
        """
        graph = self.restore(graph_id, stage=to_stage)
        if not graph:
            return None

        stages = graph.parallel_stages()
        tasks_to_reset: set[str] = set()
        for stage_idx in range(to_stage + 1, len(stages)):
            if stage_idx < len(stages):
                tasks_to_reset.update(stages[stage_idx])

        from runtime.task_graph.dag import TaskStatus
        for task_id in tasks_to_reset:
            if task_id in graph.nodes:
                node = graph.nodes[task_id]
                node.status = TaskStatus.PENDING
                node.result = None
                node.error = None
                node.started_at = None
                node.completed_at = None
                node.attempts = 0

        return graph

    def list_checkpoints(self, graph_id: str) -> list[dict[str, Any]]:
        """List all checkpoints for a graph."""
        graph_dir = self._graph_dir(graph_id)
        if not graph_dir.exists():
            return []

        checkpoints: list[dict[str, Any]] = []
        for path in sorted(graph_dir.glob("stage_*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                checkpoints.append({
                    "id": data.get("id", ""),
                    "stage": data.get("stage", 0),
                    "created_at": data.get("created_at", ""),
                    "progress": data.get("graph_data", {}).get("progress", {}),
                })
            except (json.JSONDecodeError, OSError):
                continue

        return checkpoints

    def cleanup(self, graph_id: str, keep_latest: int = 5) -> int:
        """Remove old checkpoints, keeping only the N most recent."""
        graph_dir = self._graph_dir(graph_id)
        if not graph_dir.exists():
            return 0

        stage_files = sorted(graph_dir.glob("stage_*.json"))
        if len(stage_files) <= keep_latest:
            return 0

        to_remove = stage_files[:-keep_latest]
        for path in to_remove:
            path.unlink()

        return len(to_remove)

    def purge(self, graph_id: str) -> bool:
        """Remove all checkpoints for a graph."""
        graph_dir = self._graph_dir(graph_id)
        if graph_dir.exists():
            shutil.rmtree(graph_dir)
            return True
        return False

    def list_graphs(self) -> list[dict[str, Any]]:
        """List all graphs that have checkpoints."""
        if not self.checkpoint_dir.exists():
            return []

        graphs: list[dict[str, Any]] = []
        for path in sorted(self.checkpoint_dir.iterdir()):
            if path.is_dir():
                latest = path / "latest.json"
                if latest.exists():
                    try:
                        data = json.loads(latest.read_text(encoding="utf-8"))
                        graphs.append({
                            "graph_id": path.name,
                            "latest_stage": data.get("stage", 0),
                            "created_at": data.get("created_at", ""),
                            "progress": data.get("graph_data", {}).get("progress", {}),
                        })
                    except (json.JSONDecodeError, OSError):
                        graphs.append({"graph_id": path.name, "error": "corrupt"})

        return graphs
