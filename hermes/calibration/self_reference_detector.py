"""Self-reference and cycle detection."""

from __future__ import annotations

from typing import Any


def detect_self_reference(edges: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    cycles = []
    for source, outgoing in edges.items():
        for edge in outgoing:
            target = edge["target"]
            if target == source:
                cycles.append([source, target])
            for reverse in edges.get(target, []):
                if reverse["target"] == source:
                    cycles.append([source, target, source])
    return {
        "self_reference": bool(cycles),
        "cycles": cycles,
        "trust_reduction_event": bool(cycles),
    }
