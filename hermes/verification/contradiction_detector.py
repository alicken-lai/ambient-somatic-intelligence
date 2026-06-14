"""Contradiction detection for claims and evidence."""

from __future__ import annotations

from hermes.verification.claims import Claim
from hermes.verification.evidence import Evidence


NEGATIONS = ["not ", "never ", "no ", "without ", "cannot "]


def detect_contradiction(claim: Claim, evidence: Evidence | None = None, other_claim: Claim | None = None, guardian_status: str | None = None) -> dict[str, object]:
    if guardian_status in {"BLOCK", "REVIEW_REQUIRED"} and claim.claim_type in {"recommendation", "policy", "governance"}:
        return {"contradiction": True, "severity": "high", "reason": f"Guardian status {guardian_status} conflicts with action-like claim."}
    target_text = evidence.source_reference if evidence else (other_claim.claim_text if other_claim else "")
    if target_text and _opposite_polarity(claim.claim_text.lower(), target_text.lower()):
        return {"contradiction": True, "severity": "medium", "reason": "Claim and evidence/claim have opposite polarity."}
    return {"contradiction": False, "severity": "none", "reason": "No contradiction detected."}


def _opposite_polarity(a: str, b: str) -> bool:
    a_neg = any(token in a for token in NEGATIONS)
    b_neg = any(token in b for token in NEGATIONS)
    shared = set(a.split()).intersection(set(b.split()))
    return bool(shared) and a_neg != b_neg
