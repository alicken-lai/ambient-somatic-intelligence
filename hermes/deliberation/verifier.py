"""Verifier stage for ASI deliberation."""

from __future__ import annotations

from typing import Any


def verify_claims(claims: list[str], evidence: dict[str, Any] | None = None) -> list[dict[str, str]]:
    evidence = evidence or {}
    results: list[dict[str, str]] = []
    for claim in claims:
        key = claim.lower()
        if key in evidence:
            status = "verified" if evidence[key] else "contradicted"
            note = "checked against supplied evidence"
        else:
            status = "not_checked"
            note = "no allowed-tool evidence supplied"
        results.append({"claim": claim, "status": status, "evidence_note": note})
    return results
