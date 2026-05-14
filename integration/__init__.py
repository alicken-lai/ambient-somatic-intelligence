"""
integration — v0.4 cross-subsystem integration layer.

Provides typed event contracts, bus wiring, and boot/verify for the
four v0.4 subsystems: skills, attention, somatic memory, and skillify.

Usage:
    from integration.v04_boot import boot_v04, verify_v04

    v04 = boot_v04(kernel)
    report = verify_v04(kernel, v04)
"""

from __future__ import annotations

__all__ = [
    "v04_contracts",
    "v04_wiring",
    "v04_boot",
    "integration_map",
]
