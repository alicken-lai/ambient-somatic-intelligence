"""
Arbitration explainer — narrates a SalienceArbitrationResult.

Explains how competing domain claims were fairly blended into a single
arbitrated salience, with an explicit disclaimer that the outcome is advisory
and probabilistic rather than a deterministic verdict.
"""

from __future__ import annotations

from typing import Any

DISCLAIMER = "advisory_probabilistic_blend_not_deterministic_authority"


class ArbitrationExplainer:
    """Transparent breakdown of a fair salience arbitration."""

    def explain_arbitration(self, result: Any) -> dict[str, Any]:
        arbitrated = float(getattr(result, "arbitrated_salience", 0.0))
        fairness = float(getattr(result, "fairness_score", 0.0))
        sovereignty_ok = bool(getattr(result, "sovereignty_ok", True))
        domain_weights = dict(getattr(result, "domain_weights", {}) or {})
        claims = list(getattr(result, "claims", []) or [])

        dominant_domain = ""
        if domain_weights:
            dominant_domain = max(domain_weights, key=domain_weights.get)

        summary = (
            f"Arbitrated {len(claims)} claim(s) across {len(domain_weights)} domain(s) "
            f"into salience={arbitrated:.4f} (fairness={fairness:.4f}, "
            f"sovereignty_ok={sovereignty_ok})."
        )

        return {
            "arbitrated_salience": round(arbitrated, 4),
            "fairness_score": round(fairness, 4),
            "sovereignty_ok": sovereignty_ok,
            "domain_weights": {k: round(float(v), 4) for k, v in domain_weights.items()},
            "dominant_domain": dominant_domain,
            "claim_count": len(claims),
            "summary": summary,
            "disclaimer": DISCLAIMER,
        }
