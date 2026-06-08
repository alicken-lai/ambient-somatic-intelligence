"""
Runtime external reasoning — explains observational runtime-external influence.

Narrates how external influence observed at runtime stays sandbox-contained and
observational: it never executes, mutates state, or overrides governance.
"""

from __future__ import annotations

from typing import Any


class RuntimeExternalReasoning:
    """Explains the observational runtime-external facet of a decision."""

    def explain_decision(
        self,
        decision: Any,
        *,
        runtime_observability: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        obs = runtime_observability
        if obs is None:
            obs = getattr(decision, "runtime_external_observability", None) or {}
        sandbox_contained = True
        if isinstance(obs, dict):
            sandbox_contained = bool(obs.get("sandbox_contained", True))

        summary = (
            f"Runtime external influence is observational only "
            f"(sandbox_contained={sandbox_contained}); it never executes or "
            "overrides governance."
        )

        return {
            "advisory_only": True,
            "observational": True,
            "sandbox_contained": sandbox_contained,
            "summary": summary,
        }
