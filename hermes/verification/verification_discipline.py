"""Verification discipline policy."""

from __future__ import annotations

from hermes.verification.claims import Claim


def verification_requirement(claim: Claim) -> dict[str, object]:
    if claim.risk_level == "high" or claim.claim_type in {"security", "governance", "policy"}:
        return {"required": True, "level": "required", "reason": "High-risk, security, provider, or governance claim."}
    if claim.claim_type == "architecture":
        return {"required": True, "level": "preferred", "reason": "Architecture claims should be supported when possible."}
    return {"required": claim.verification_required, "level": "optional", "reason": "Low-risk claim or opinion."}
