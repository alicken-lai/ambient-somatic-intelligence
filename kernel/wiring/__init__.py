"""Reversible method/callback patch registry for kernel integration wiring."""

from kernel.wiring.patch_handle import PatchHandle
from kernel.wiring.patch_registry import PatchRegistry, get_patch_registry
from kernel.wiring.reversible_patch import (
    apply_callback_patch,
    apply_method_patch,
    restore_phase,
)

__all__ = [
    "PatchHandle",
    "PatchRegistry",
    "get_patch_registry",
    "apply_method_patch",
    "apply_callback_patch",
    "restore_phase",
]
