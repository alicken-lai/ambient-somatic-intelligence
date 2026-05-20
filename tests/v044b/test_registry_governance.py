"""Phase 2 — RegistryGuard on patch/truth/event registries."""

from __future__ import annotations

from architecture.bus_decomposition.event_schema import BusEventSchema, EventSchemaRegistry
from kernel.isolation.registry_guard import RegistryGuard
from kernel.isolation.write_target import WriteTarget
from kernel.truth.truth_registry import SubsystemDomain, TruthRegistry
from kernel.wiring.patch_handle import PatchHandle
from kernel.wiring.patch_registry import PatchRegistry


def test_patch_registry_guarded_register(governed_context):
    guard = RegistryGuard()
    guard.bind("patch_registry", write_target=WriteTarget.INTEGRATION_BUS, owner="test")
    reg = PatchRegistry(registry_guard=guard)

    class Target:
        value = 1

    target = Target()
    handle = PatchHandle(
        patch_id="t1",
        target=target,
        attr_name="value",
        original=1,
        replacement=2,
        phase="test",
    )
    reg.register(handle, execution_context=governed_context)
    assert target.value == 2


def test_truth_registry_guarded(governed_context):
    reg = TruthRegistry()
    result = reg.register(
        SubsystemDomain.MEMORY,
        node_id="n1",
        source="test",
        owner="test",
        version="1",
        mutability=__import__(
            "kernel.truth.truth_node", fromlist=["Mutability"]
        ).Mutability.VERSIONED,
        execution_context=governed_context,
    )
    assert result.valid


def test_event_schema_registry_guarded(governed_context):
    reg = EventSchemaRegistry()
    schema = BusEventSchema(
        name="test_conn",
        source_subsystem="test",
        target_subsystem="test",
        payload_type="dict",
        description="test",
        mechanism="callback",
        version="v0.4.4b",
        is_bidirectional=False,
        payload_fields=(),
    )
    reg.register_schema(schema, execution_context=governed_context)
    assert reg.get_schema("test_conn") is not None
