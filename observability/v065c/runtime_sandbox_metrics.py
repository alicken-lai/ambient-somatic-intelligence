"""Runtime sandbox containment metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.external.runtime.external_runtime_sandbox import ExternalRuntimeSandbox

_CLEAN = "Advisory runtime hint: think before coding."
_DIRTY = "exec(os.system('rm -rf /'))"


@dataclass
class RuntimeSandboxMetrics:
    containment_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"containment_rate": round(self.containment_rate, 4)}


def collect_runtime_sandbox_metrics() -> RuntimeSandboxMetrics:
    sb = ExternalRuntimeSandbox()
    passed = 0
    total = 2
    if sb.evaluate(_CLEAN).contained:
        passed += 1
    if not sb.evaluate(_DIRTY).contained:
        passed += 1
    return RuntimeSandboxMetrics(containment_rate=passed / total)
