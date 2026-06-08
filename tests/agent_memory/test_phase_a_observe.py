"""Phase A (observe-only) tests for the agent-memory ontology back-door fix.

These tests pin down two things:
  1. The new observability surface works (layer labelling, decay projection,
     and init-bypass detection).
  2. Phase A does NOT change existing behavior: confidence is still stored
     verbatim (the back door is observed, not yet closed) and recall/eviction
     are untouched. Enforcement is deferred to a later, governed phase.
"""

from __future__ import annotations

from datetime import timedelta, timezone, datetime

import pytest

import agents.memory as agent_memory
from agents.memory import AgentMemory, MemoryEntry, category_to_layer


@pytest.fixture
def mem(tmp_path, monkeypatch) -> AgentMemory:
    # Phase B enforcement is now ON by default; these Phase A tests validate the
    # observe-only ROLLBACK path, so we explicitly disable enforcement here.
    monkeypatch.setenv("AMBIENT_OS_MEMORY_ENFORCE", "0")
    monkeypatch.setattr(agent_memory, "AGENTS_MEMORY_DIR", tmp_path)
    return AgentMemory("test-agent")


def test_category_to_layer_mapping():
    assert category_to_layer("knowledge") == 1
    assert category_to_layer("pattern") == 1
    assert category_to_layer("failure") == 2
    assert category_to_layer("skill") == 3
    assert category_to_layer("strategy") == 4
    assert category_to_layer("unknown-thing") == 1  # safe default


def test_remember_labels_layer(mem: AgentMemory):
    strat = mem.remember("use X for Y", category="strategy")
    know = mem.remember("fact about Z", category="knowledge")
    assert strat.layer == 4
    assert know.layer == 1
    assert strat.entry_id and know.entry_id
    assert strat.entry_id != know.entry_id


def test_rollback_preserves_phase_a_semantics(mem: AgentMemory):
    """With enforcement disabled, remember() keeps the Phase A observe semantics:
    confidence is stored verbatim and category maps straight to layer.
    """
    e = mem.remember("instant strategy", category="strategy", confidence=1.0)
    assert e.confidence == 1.0
    assert e.layer == 4


def test_integrity_warnings_flags_init_bypass(mem: AgentMemory):
    mem.remember("Tailwind @apply reduces duplication", category="strategy", confidence=1.0)
    mem.remember("React useCallback basics", category="knowledge", confidence=1.0)
    warnings = mem.integrity_warnings()
    assert len(warnings) == 1
    w = warnings[0]
    assert w["category"] == "strategy"
    assert w["layer"] == 4
    assert "init-bypass" in w["reason"]


def test_integrity_warnings_ignores_used_entries(mem: AgentMemory):
    mem.remember("validated skill", category="skill", confidence=1.0)
    # Simulate real usage -> should no longer look like an injection.
    mem.recall("validated skill")
    assert mem.integrity_warnings() == []


def test_decay_report_is_observe_only(mem: AgentMemory):
    e = mem.remember("aging knowledge", category="knowledge", confidence=0.8)
    before_conf = e.confidence
    before_count = len(mem._entries)

    future = datetime.now(tz=timezone.utc) + timedelta(days=120)
    reports = mem.decay_report(now=future)

    # Read-only: nothing mutated, nothing discarded.
    assert e.confidence == before_conf
    assert len(mem._entries) == before_count

    if reports:  # ontology available
        r = next(r for r in reports if r["entry_id"] == e.entry_id)
        assert r["projected_confidence"] <= r["current_confidence"]
        assert r["recommended_action"] in {"retain", "archive", "remove"}


def test_serialization_roundtrip_preserves_new_fields(mem: AgentMemory):
    e = mem.remember("roundtrip", category="strategy", confidence=0.7)
    data = e.to_dict()
    assert data["layer"] == 4
    assert data["entry_id"] == e.entry_id
    restored = MemoryEntry.from_dict(data)
    assert restored.layer == 4
    assert restored.entry_id == e.entry_id
    assert restored.confidence == 0.7


def test_legacy_entry_without_new_fields_loads_safely():
    """Old entries.jsonl rows have no layer/entry_id; they must still load."""
    legacy = {
        "content": "legacy strategy",
        "category": "strategy",
        "tags": [],
        "confidence": 1.0,
        "uses": 0,
        "last_used": 0,
        "created": 1_700_000_000.0,
        "metadata": {},
    }
    e = MemoryEntry.from_dict(legacy)
    assert e.layer == 4  # inferred from category
    assert len(e.entry_id) == 12  # generated


def test_recall_behavior_unchanged(mem: AgentMemory):
    mem.remember("react performance hooks", category="knowledge", tags=["react"])
    results = mem.recall("react performance")
    assert len(results) == 1
    assert results[0].uses == 1  # recall still increments uses
