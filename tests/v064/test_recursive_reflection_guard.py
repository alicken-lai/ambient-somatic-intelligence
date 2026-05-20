"""Area 5b: recursive reflection guard."""

from governance.metacognition.recursive_reflection_guard import RecursiveReflectionGuard


def test_blocked_routes() -> None:
    rg = RecursiveReflectionGuard()
    for route in ("metacognitive_reflect", "reflection_on_reflection"):
        assert rg.block_recursive_route(route) is True


def test_chain_blocks_deep_reflect() -> None:
    rg = RecursiveReflectionGuard()
    rg.record("telemetry_reflect")
    rg.record("coherence_reflect")
    assert rg.block_recursive_route("nested_reflect") is True
