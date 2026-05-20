"""Reversible wiring: wire/unwire cycles restore methods and callbacks."""

from __future__ import annotations

import pytest

from integration.v04_wiring import V04Wiring, unwire_v04, wire_v04
from kernel import AmbientKernel
from kernel.wiring import get_patch_registry


class TestPatchRegistry:
    def test_method_patch_restore(self):
        from kernel.wiring import apply_method_patch

        class Target:
            def method(self):
                return "original"

        t = Target()
        original = t.method

        def replacement(*args, **kwargs):
            return "patched"

        apply_method_patch(
            t,
            "method",
            replacement,
            patch_id="test.target.method",
            phase="test",
        )
        assert t.method() == "patched"
        get_patch_registry().restore_phase("test")
        assert t.method() == "original"
        assert not get_patch_registry().is_active("test.target.method")


class TestIntegrationBusV04Reversible:
    def test_wire_unwire_three_cycles_no_active_patches(self):
        k = AmbientKernel.boot()
        bus = k.integration_bus
        original_log = bus._log_event
        original_health = k.health

        for _ in range(3):
            bus.wire_v04()
            reg = get_patch_registry()
            assert reg.is_active("integration_bus._log_event")
            bus.unwire_v04()
            assert not reg.is_active("integration_bus._log_event")
            assert bus._v04_stabilization is None

        assert bus._log_event == original_log
        assert k.health == original_health

    def test_no_duplicate_patch_ids_on_rewire(self):
        k = AmbientKernel.boot()
        bus = k.integration_bus
        reg = get_patch_registry()

        for _ in range(3):
            bus.wire_v04()
            active = reg.active_patch_ids("v04_bus")
            assert len(active) == len(set(active))
            bus.unwire_v04()

        assert reg.active_patch_ids("v04_bus") == []


class TestV04IntegrationWiringReversible:
    @pytest.fixture
    def minimal_v04(self):
        """Minimal V04Subsystems stand-ins for wiring tests."""
        from types import SimpleNamespace

        k = AmbientKernel.boot()

        class _Router:
            def execute_with_fallback(self, decision, context, **kwargs):
                return decision

        class _Escalation:
            def evaluate(self, *args, **kwargs):
                return SimpleNamespace(
                    action="log",
                    signal_id="sig-test",
                    reason="test",
                    salience_total=0.1,
                )

        class _Store:
            def store(self, episode, **kwargs):
                return episode

        class _Matcher:
            def match(self, *args, **kwargs):
                return []

        class _Pipeline:
            def propose(self, candidate, **kwargs):
                return SimpleNamespace(status="pending_review", proposal_id="p1")

        class _Observer:
            def __init__(self):
                self._events = []

            def observe(self, event, **kwargs):
                self._events.append(event)
                return event

            def recent(self, limit=50):
                return self._events[-limit:]

        class _Miner:
            def mine(self, events, min_support=3):
                return []

        v04 = SimpleNamespace(
            salience_engine=SimpleNamespace(compute_salience=lambda *a, **k: None),
            escalation_router=_Escalation(),
            skill_router=_Router(),
            somatic_episode_store=_Store(),
            precursor_matcher=_Matcher(),
            skill_registration_pipeline=_Pipeline(),
            workflow_observer=_Observer(),
            pattern_miner=_Miner(),
        )
        return k, v04

    def test_wire_unwire_three_cycles_integration_patches(
        self, minimal_v04,
    ):
        k, v04 = minimal_v04
        bus = k.integration_bus
        reg = get_patch_registry()

        original_evaluate = v04.escalation_router.evaluate
        original_execute = v04.skill_router.execute_with_fallback

        for _ in range(3):
            wiring = wire_v04(k, bus, v04)
            assert wiring.is_active
            assert reg.is_active("v04.escalation_router.evaluate")
            unwire_v04(wiring, bus)
            assert not wiring.is_active
            assert not reg.is_active("v04.escalation_router.evaluate")

        assert reg.active_patch_ids("v04_integration") == []
        assert v04.escalation_router.evaluate() is not None
        assert callable(v04.escalation_router.evaluate)
        assert callable(v04.skill_router.execute_with_fallback)
        assert v04.escalation_router.evaluate.__name__ == original_evaluate.__name__
        assert v04.skill_router.execute_with_fallback.__name__ == original_execute.__name__

    def test_somatic_callback_removed_after_unwire(self, minimal_v04):
        k, v04 = minimal_v04
        bus = k.integration_bus
        somatic_bus = k.somatic.bus
        before = len(somatic_bus._any_handlers)

        wiring = wire_v04(k, bus, v04)
        assert len(somatic_bus._any_handlers) >= before + 1

        unwire_v04(wiring, bus)
        assert len(somatic_bus._any_handlers) == before
