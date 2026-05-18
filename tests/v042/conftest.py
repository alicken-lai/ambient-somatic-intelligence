"""Shared fixtures for v0.4.2 entropy tests."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from kernel.entropy import EntropyController
from kernel.entropy.stale_state_detector import StaleStateDetector
from kernel.truth import Mutability, TruthGraph, TruthNode
from kernel.v04_stabilization import boot_stabilization


@pytest.fixture
def fresh_root(tmp_path: Path) -> Path:
    now = datetime.now(timezone.utc).isoformat()
    (tmp_path / "state").mkdir()
    (tmp_path / "memory").mkdir()
    (tmp_path / "state" / "system_state.json").write_text(
        json.dumps({"updated_at": now}),
        encoding="utf-8",
    )
    (tmp_path / "memory" / "dmn.jsonl").write_text(
        json.dumps({"timestamp": now}) + "\n",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def truth_graph() -> TruthGraph:
    graph = TruthGraph()
    node = TruthNode.create(
        node_id="test:baseline",
        source="tests.v042",
        owner="tests",
        version="1.0",
        mutability=Mutability.IMMUTABLE,
        payload={"ok": True},
    )
    graph.register_node(node)
    return graph


@pytest.fixture
def entropy_controller(fresh_root: Path) -> EntropyController:
    return EntropyController(stale_detector=StaleStateDetector(fresh_root))
