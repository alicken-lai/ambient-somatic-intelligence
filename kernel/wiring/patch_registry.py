"""Central registry of all integration patches."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kernel.wiring.patch_handle import PatchHandle

_global_registry: PatchRegistry | None = None
_registry_lock = threading.Lock()


class PatchRegistry:
    """Tracks active patches by id and phase for reversible wire/unwire cycles."""

    def __init__(self, registry_guard: Any | None = None) -> None:
        self._patches: dict[str, PatchHandle] = {}
        self._active_order: list[str] = []
        self._registry_guard = registry_guard
        if self._registry_guard is None:
            try:
                from kernel.isolation.registry_guard import RegistryGuard
                from kernel.isolation.write_target import WriteTarget

                guard = RegistryGuard()
                guard.bind("patch_registry", write_target=WriteTarget.INTEGRATION_BUS, owner="kernel")
                self._registry_guard = guard
            except ImportError:
                self._registry_guard = None

    def register(
        self,
        handle: PatchHandle,
        execution_context: Any | None = None,
    ) -> PatchHandle:
        """Register a method patch; if the same patch_id is active, restore it first."""
        def _register() -> PatchHandle:
            existing = self._patches.get(handle.patch_id)
            if existing is not None and existing.is_active:
                existing.restore()
                if handle.patch_id in self._active_order:
                    self._active_order.remove(handle.patch_id)

            setattr(handle.target, handle.attr_name, handle.replacement)
            self._patches[handle.patch_id] = handle
            if handle.patch_id not in self._active_order:
                self._active_order.append(handle.patch_id)
            return handle

        if execution_context is not None and self._registry_guard is not None:
            return self._registry_guard.mutate(
                "patch_registry",
                _register,
                context=execution_context,
                operation="register",
            )
        return _register()

    def register_callback(
        self,
        handle: PatchHandle,
        execution_context: Any | None = None,
    ) -> PatchHandle:
        """Register a callback patch (no setattr — removal via callback_remover)."""
        def _register() -> PatchHandle:
            existing = self._patches.get(handle.patch_id)
            if existing is not None and existing.is_active:
                existing.restore()
                if handle.patch_id in self._active_order:
                    self._active_order.remove(handle.patch_id)

            self._patches[handle.patch_id] = handle
            if handle.patch_id not in self._active_order:
                self._active_order.append(handle.patch_id)
            return handle

        if execution_context is not None and self._registry_guard is not None:
            return self._registry_guard.mutate(
                "patch_registry",
                _register,
                context=execution_context,
                operation="register_callback",
            )
        return _register()

    def get(self, patch_id: str) -> PatchHandle | None:
        return self._patches.get(patch_id)

    def is_active(self, patch_id: str) -> bool:
        handle = self._patches.get(patch_id)
        return handle is not None and handle.is_active

    def active_patch_ids(self, phase: str | None = None) -> list[str]:
        ids: list[str] = []
        for patch_id in self._active_order:
            handle = self._patches.get(patch_id)
            if handle is None or not handle.is_active:
                continue
            if phase is None or handle.phase == phase:
                ids.append(patch_id)
        return ids

    def restore(self, patch_id: str) -> bool:
        handle = self._patches.get(patch_id)
        if handle is None or not handle.is_active:
            return False
        handle.restore()
        if patch_id in self._active_order:
            self._active_order.remove(patch_id)
        return True

    def restore_phase(self, phase: str) -> int:
        """Restore all active patches in a phase (reverse registration order)."""
        restored = 0
        for patch_id in reversed(list(self._active_order)):
            handle = self._patches.get(patch_id)
            if handle is None or not handle.is_active or handle.phase != phase:
                continue
            if handle.restore():
                restored += 1
                self._active_order.remove(patch_id)
        return restored

    def restore_all(self) -> int:
        restored = 0
        for patch_id in reversed(list(self._active_order)):
            if self.restore(patch_id):
                restored += 1
        self.clear_inactive()
        return restored

    def clear_inactive(self) -> None:
        inactive = [
            pid for pid, h in self._patches.items()
            if not h.is_active
        ]
        for pid in inactive:
            del self._patches[pid]

    def entropy_snapshot(self) -> dict[str, Any]:
        """Read-only observability snapshot for entropy adapters."""
        import time

        handles = list(self._patches.values())
        active = [h for h in handles if h.is_active]
        inactive_registered = sum(1 for h in handles if not h.is_active)
        target_keys: list[str] = []
        ages: list[float] = []
        now = time.time()
        for handle in active:
            if handle.callback_remover is None:
                target_keys.append(f"{id(handle.target)}:{handle.attr_name}")
            ages.append(max(0.0, now - handle.timestamp))

        overlap = max(0, len(target_keys) - len(set(target_keys)))
        restored = sum(1 for h in handles if h.restored)
        if not active:
            unwire_ratio = 1.0
        else:
            attempted_restore = restored + len(active)
            unwire_ratio = restored / attempted_restore if attempted_restore else 1.0

        return {
            "total_count": len(handles),
            "active_count": len(active),
            "inactive_but_registered": inactive_registered,
            "register_churn": len(handles),
            "target_overlap": overlap,
            "mean_age_seconds": sum(ages) / len(ages) if ages else 0.0,
            "unwire_success_ratio": unwire_ratio,
        }


def get_patch_registry() -> PatchRegistry:
    """Process-wide patch registry singleton."""
    global _global_registry
    if _global_registry is None:
        with _registry_lock:
            if _global_registry is None:
                _global_registry = PatchRegistry()
    return _global_registry
