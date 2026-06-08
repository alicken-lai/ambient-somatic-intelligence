"""Phase B (enforce-by-default) tests for the agent-memory backdoor fix.

Covers the DEFAULT behavior change:
  - remember() forces L1 + caps initial confidence; high layer is only a
    candidate target (metadata['target_layer']);
  - seed_knowledge() always lands at L1 with capped confidence;
  - promote() enforces the ontology gate plus governance + independent-verifier
    rules (no self-verification);
  - the emergency rollback env restores Phase A observe semantics.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import agents.memory as agent_memory
from agents.memory import AgentMemory, MemoryEntry
from memory.ontology.layer_definition import MemoryLayer


@pytest.fixture
def mem(tmp_path, monkeypatch) -> AgentMemory:
    # Enforcement is ON by default; pin it explicitly so other tests setting the
    # env cannot leak into these.
    monkeypatch.setenv("AMBIENT_OS_MEMORY_ENFORCE", "1")
    monkeypatch.setattr(agent_memory, "AGENTS_MEMORY_DIR", tmp_path)
    return AgentMemory("frontend-agent")


# --- remember() default behavior change ------------------------------------

def test_remember_forces_l1_and_caps_confidence(mem: AgentMemory):
    e = mem.remember("Use Tailwind @apply for repeats", category="strategy", confidence=1.0)
    assert e.layer == 1
    assert e.confidence == 0.5
    assert e.metadata["target_layer"] == 4
    assert e.metadata["author"] == "frontend-agent"


def test_remember_low_confidence_is_not_raised(mem: AgentMemory):
    e = mem.remember("a fact", category="knowledge", confidence=0.3)
    assert e.layer == 1
    assert e.confidence == 0.3  # cap only lowers, never raises
    assert "target_layer" not in e.metadata  # L1 request has no target


def test_fresh_strategy_no_longer_trips_integrity_warning(mem: AgentMemory):
    mem.remember("instant strategy", category="strategy", confidence=1.0)
    assert mem.integrity_warnings() == []


# --- seed_knowledge() -------------------------------------------------------

def test_seed_knowledge_forces_l1_and_marks_origin(mem: AgentMemory):
    e = mem.seed_knowledge("preloaded fact", confidence=1.0)
    assert e.layer == 1
    assert e.confidence == 0.5
    assert e.metadata["origin"] == "preloaded"


# --- promote() gate ---------------------------------------------------------

def test_promote_blocks_insufficient_evidence(mem: AgentMemory):
    e = mem.remember("candidate", category="strategy", confidence=1.0)  # L1, conf 0.5, uses 0
    result = mem.promote(e, MemoryLayer.L2_INSTINCT)
    assert result.ok is False
    assert result.blocking_reasons  # confidence + occurrences too low
    assert e.layer == 1  # unchanged


def test_promote_rejects_non_single_step(mem: AgentMemory):
    e = mem.remember("candidate", category="knowledge")
    result = mem.promote(e, MemoryLayer.L4_STRATEGIC)
    assert result.ok is False
    assert any("single-step" in r for r in result.blocking_reasons)


def test_promote_l1_to_l2_succeeds_when_eligible(mem: AgentMemory):
    e = mem.remember("repeated pattern", category="knowledge")
    # Simulate accrued evidence meeting the L1->L2 rule (conf>=0.7, occ>=3).
    e.confidence = 0.8
    e.uses = 3
    result = mem.promote(e, MemoryLayer.L2_INSTINCT)
    assert result.ok is True
    assert result.to_layer == 2
    assert e.layer == 2
    assert e.metadata["promoted_from"] == 1


def _make_l3_candidate(mem: AgentMemory) -> MemoryEntry:
    e = mem.remember("validated skill", category="knowledge")
    e.layer = 3
    e.confidence = 0.95
    e.uses = 10
    e.success_count = 10
    e.failure_count = 0
    e.contexts_validated = ["web", "mobile"]
    e.metadata["author"] = "frontend-agent"
    return e


def test_promote_l3_to_l4_requires_governance(mem: AgentMemory):
    e = _make_l3_candidate(mem)
    result = mem.promote(e, MemoryLayer.L4_STRATEGIC,
                         verifier=SimpleNamespace(identity="reviewer"))
    assert result.ok is False
    assert any("governance" in r for r in result.blocking_reasons)
    assert e.layer == 3


def test_promote_l3_to_l4_requires_verifier(mem: AgentMemory):
    e = _make_l3_candidate(mem)
    result = mem.promote(e, MemoryLayer.L4_STRATEGIC, governance_token="ALLOW")
    assert result.ok is False
    assert any("verifier" in r for r in result.blocking_reasons)
    assert e.layer == 3


def test_promote_l3_to_l4_rejects_self_verification(mem: AgentMemory):
    e = _make_l3_candidate(mem)  # author == "frontend-agent"
    result = mem.promote(e, MemoryLayer.L4_STRATEGIC, governance_token="ALLOW",
                         verifier=SimpleNamespace(identity="frontend-agent"))
    assert result.ok is False
    assert any("self-verification" in r for r in result.blocking_reasons)
    assert e.layer == 3


def test_promote_l3_to_l4_succeeds_with_independent_verifier(mem: AgentMemory):
    e = _make_l3_candidate(mem)
    result = mem.promote(e, MemoryLayer.L4_STRATEGIC, governance_token="ALLOW",
                         verifier=SimpleNamespace(identity="independent-reviewer"))
    assert result.ok is True
    assert result.to_layer == 4
    assert e.layer == 4


# --- rollback + serialization ----------------------------------------------

def test_rollback_env_restores_phase_a_behavior(tmp_path, monkeypatch):
    monkeypatch.setenv("AMBIENT_OS_MEMORY_ENFORCE", "0")
    monkeypatch.setattr(agent_memory, "AGENTS_MEMORY_DIR", tmp_path)
    m = AgentMemory("rollback-agent")
    e = m.remember("legacy-style strategy", category="strategy", confidence=1.0)
    assert e.layer == 4
    assert e.confidence == 1.0


def test_serialization_roundtrip_includes_phase_b_fields(mem: AgentMemory):
    e = mem.remember("roundtrip", category="knowledge")
    e.success_count = 4
    e.failure_count = 1
    e.contexts_validated = ["web"]
    data = e.to_dict()
    restored = MemoryEntry.from_dict(data)
    assert restored.success_count == 4
    assert restored.failure_count == 1
    assert restored.contexts_validated == ["web"]
    assert abs(restored.success_rate() - 0.8) < 1e-9
