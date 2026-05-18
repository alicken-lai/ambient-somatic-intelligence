"""Mutation hook pressure."""

from __future__ import annotations

from kernel.entropy.mutation_tracker import MutationTracker


def test_mutation_hook_pressure() -> None:
    tracker = MutationTracker()
    tracker.observe_global_mutation("CONFIG", caller="test")
    tracker.observe_singleton_rewrite("get_memory_kernel", caller="test")
    tracker.observe_callback_growth(5)
    tracker.observe_registry_mutation("PatchRegistry", "register", caller="test")

    metrics = {m.name: m for m in tracker.observe()}
    assert metrics["mutation_hook_pressure"].value > 0
    stats = tracker.stats()
    assert stats["global_mutations"] == 1
    assert stats["callback_growth"] == 5
