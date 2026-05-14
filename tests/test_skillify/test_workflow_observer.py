"""Tests for agents.skillify.workflow_observer — Observation recording, querying."""

from __future__ import annotations

from pathlib import Path

from agents.skillify.workflow_observer import (
    WorkflowEvent,
    WorkflowObserver,
    WorkflowStep,
)


def _make_event(
    workflow_type: str = "anomaly_detection",
    success: bool = True,
) -> WorkflowEvent:
    return WorkflowEvent.create(
        workflow_type=workflow_type,
        steps=[
            WorkflowStep("step1", "mod", "fn", 100.0, True),
            WorkflowStep("step2", "mod", "fn", 200.0, success),
        ],
        inputs={"description": "test task"},
        outputs={"result": "ok"},
        success=success,
        duration_ms=300.0,
    )


def test_observe_records(tmp_dir: Path) -> None:
    """Observe workflow events and verify they are stored."""
    observer = WorkflowObserver(storage_path=tmp_dir / "obs.jsonl")
    event = _make_event()
    observer.observe(event)

    assert observer.count() == 1
    recent = observer.recent(5)
    assert len(recent) == 1
    assert recent[0].event_id == event.event_id


def test_query_by_type(tmp_dir: Path) -> None:
    """Filter observations by workflow_type."""
    observer = WorkflowObserver(storage_path=tmp_dir / "obs.jsonl")
    observer.observe(_make_event("anomaly_detection"))
    observer.observe(_make_event("anomaly_detection"))
    observer.observe(_make_event("health_check"))

    results = observer.query(workflow_type="anomaly_detection")
    assert len(results) == 2

    results_hc = observer.query(workflow_type="health_check")
    assert len(results_hc) == 1


def test_query_by_success(tmp_dir: Path) -> None:
    """Filter by success status."""
    observer = WorkflowObserver(storage_path=tmp_dir / "obs.jsonl")
    observer.observe(_make_event(success=True))
    observer.observe(_make_event(success=False))

    successes = observer.query(success=True)
    assert len(successes) == 1

    failures = observer.query(success=False)
    assert len(failures) == 1


def test_persistence(tmp_dir: Path) -> None:
    """Events survive observer reconstruction from disk."""
    path = tmp_dir / "obs.jsonl"
    obs1 = WorkflowObserver(storage_path=path)
    obs1.observe(_make_event("type_a"))
    obs1.observe(_make_event("type_b"))

    obs2 = WorkflowObserver(storage_path=path)
    assert obs2.count() == 2
    assert set(obs2.workflow_types()) == {"type_a", "type_b"}
