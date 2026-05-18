"""Stale state detector."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from kernel.entropy.stale_state_detector import StaleStateDetector
from kernel.truth import TruthGraph


def test_stale_state_critical_on_missing(tmp_path: Path) -> None:
    detector = StaleStateDetector(root=tmp_path)
    report = detector.scan(TruthGraph())
    assert report.critical_count >= 1
    metrics = {m.name: m for m in detector.observe(TruthGraph())}
    assert metrics["stale_state_critical"].value >= 1.0


def test_stale_state_ok_on_fresh_files(tmp_path: Path) -> None:
    now = datetime.now(timezone.utc).isoformat()
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "system_state.json").write_text(
        json.dumps({"updated_at": now}),
        encoding="utf-8",
    )
    mem_dir = tmp_path / "memory"
    mem_dir.mkdir()
    (mem_dir / "dmn.jsonl").write_text(
        json.dumps({"timestamp": now, "content": "test"}) + "\n",
        encoding="utf-8",
    )

    detector = StaleStateDetector(root=tmp_path)
    report = detector.scan(TruthGraph())
    assert report.critical_count == 0
