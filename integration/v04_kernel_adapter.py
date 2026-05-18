"""Migration adapters — bridge integration/ package to kernel v0.4 stabilization.

Adapts existing integration/v04_wiring.py hooks to typed kernel contracts
without modifying v0.3.1 boot or ontology promotion chains.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kernel import AmbientKernel
    from kernel.integration_bus import IntegrationBus

logger = logging.getLogger("integration.v04_kernel_adapter")


def adapt_bus_event_log(bus: IntegrationBus, truth_registry: Any) -> None:
    """
    Adapter: mirror recent IntegrationBus events as truth nodes.

    Replaces implicit event history with registered truth entries.
    """
    from kernel.truth.truth_node import Mutability

    recent = bus.event_log[-20:] if bus.event_log else []
    for event in recent:
        try:
            truth_registry.register_runtime(
                node_id=f"bus_event:{event.event_type}:{int(event.timestamp)}",
                owner="kernel.integration_bus",
                version="v0.4",
                payload=event.to_dict(),
                source=event.source,
            )
        except Exception as exc:
            logger.debug("Truth adapter skipped event: %s", exc)


def adapt_v04_wiring_connections(
    bus: IntegrationBus,
    coupling_pressure: Any,
    connection_names: list[str],
) -> None:
    """Adapter: feed existing v04_wiring connection names into coupling pressure."""
    for name in connection_names:
        parts = name.split("_to_")
        if len(parts) == 2:
            coupling_pressure.record(parts[0], parts[1], mechanism="integration.v04_wiring")
    coupling_pressure.observe()
    bus._log_event(
        "integration.v04_wiring",
        "kernel.entropy.coupling_pressure",
        "coupling_adapted",
        f"{len(connection_names)} v0.4 connections indexed",
    )


def adapt_kernel_health(
    kernel: AmbientKernel,
    stabilization: Any,
) -> None:
    """Adapter: extend kernel.health() with v0.4 stabilization snapshot."""
    from kernel.wiring import apply_method_patch

    original_health = kernel.health

    def health_with_v04() -> dict:
        result = original_health()
        try:
            result["v04_stabilization"] = stabilization.snapshot()
        except Exception:
            result["v04_stabilization"] = {"error": "unavailable"}
        return result

    apply_method_patch(
        kernel,
        "health",
        health_with_v04,
        patch_id="ambient_kernel.health",
        phase="v04_bus",
    )
