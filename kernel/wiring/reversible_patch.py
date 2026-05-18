"""Helpers to apply integration patches with registry recording."""

from __future__ import annotations

import time
from typing import Any, Callable

from kernel.wiring.patch_handle import PatchHandle
from kernel.wiring.patch_registry import PatchRegistry, get_patch_registry


def apply_method_patch(
    target: Any,
    attr_name: str,
    replacement: Any,
    *,
    patch_id: str,
    phase: str,
    registry: PatchRegistry | None = None,
) -> PatchHandle:
    """
    Replace target.attr_name with replacement and record for restore().

    The replacement is typically a wrapper that closes over the original method.
    """
    reg = registry or get_patch_registry()
    original = getattr(target, attr_name)
    handle = PatchHandle(
        patch_id=patch_id,
        phase=phase,
        target=target,
        attr_name=attr_name,
        original=original,
        replacement=replacement,
        timestamp=time.time(),
    )
    return reg.register(handle)


def apply_callback_patch(
    bus: Any,
    handler: Callable[..., Any],
    *,
    patch_id: str,
    phase: str,
    registry: PatchRegistry | None = None,
) -> PatchHandle:
    """
    Register a somatic bus on_any callback with reversible removal.

    Uses SomaticSignalBus.off_any when available.
    """
    reg = registry or get_patch_registry()
    bus.on_any(handler)

    def remover() -> None:
        if hasattr(bus, "off_any"):
            bus.off_any(handler)

    handle = PatchHandle(
        patch_id=patch_id,
        phase=phase,
        target=bus,
        attr_name="on_any",
        original=None,
        replacement=handler,
        timestamp=time.time(),
        callback_remover=remover,
    )
    return reg.register_callback(handle)


def restore_phase(phase: str, registry: PatchRegistry | None = None) -> int:
    """Restore all patches registered under phase."""
    reg = registry or get_patch_registry()
    return reg.restore_phase(phase)
