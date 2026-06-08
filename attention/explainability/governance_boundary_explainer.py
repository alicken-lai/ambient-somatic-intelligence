"""
Governance boundary explainer — enumerates the layered governance boundaries.

Presents the enforcement-ordered stack a salience proposal traverses, starting
with the frozen constitutional guard. Read-only and descriptive: it documents
the boundaries, it does not enforce or weaken them.
"""

from __future__ import annotations

from typing import Any

# Frozen constitutional rules evaluated before arbitration (see ConstitutionalGuard).
CONSTITUTIONAL_RULES = (
    "guardian_supremacy",
    "epistemic_limit",
    "replay_boundary",
    "forecast_boundary",
    "self_modification",
    "no_recursive_governance",
)

# Enforcement-ordered governance layers; constitutional_guard runs first.
_LAYERS = (
    ("constitutional_guard", "enforcing", "Frozen constitution; blocks violations before arbitration."),
    ("sovereignty_limits", "enforcing", "Blocks recursive governance and over-concentrated domains."),
    ("cognitive_identity", "enforcing", "Provenance + authority multiplier; can revoke untrusted sources."),
    ("salience_arbitration", "advisory", "Fair bounded blend of competing domain claims."),
    ("cognitive_coherence", "advisory", "Damps incoherent salience after arbitration."),
    ("metacognitive_reflection", "observational", "Reflects on the decision; never overrides it."),
    ("cognitive_homeostasis", "observational", "Stabilization recommendations; never overrides."),
)


class GovernanceBoundaryExplainer:
    """Describes the layered governance boundaries in enforcement order."""

    def explain_layers(self) -> dict[str, Any]:
        layers = [
            {"name": name, "mode": mode, "description": desc}
            for name, mode, desc in _LAYERS
        ]
        return {
            "advisory_only": True,
            "no_autonomous_execution": True,
            "layer_count": len(layers),
            "constitutional_rule_count": len(CONSTITUTIONAL_RULES),
            "constitutional_rules": list(CONSTITUTIONAL_RULES),
            "layers": layers,
        }
