"""Deterministic claim extraction from deliberation artifacts."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from hermes.verification.claims.claim_models import Claim


SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")


class ClaimExtractor:
    def extract(self, artifact: Any, *, source: str = "unknown") -> list[Claim]:
        texts = list(_collect_text(artifact))
        claims: list[Claim] = []
        for text in texts:
            for sentence in [item.strip(" -\t") for item in SENTENCE_RE.split(text) if item.strip()]:
                if len(sentence) < 12:
                    continue
                claim_type = _claim_type(sentence)
                risk_level = _risk_level(sentence, claim_type)
                verification_required = risk_level in {"medium", "high"} or claim_type in {"fact", "policy", "architecture", "security", "governance"}
                claims.append(
                    Claim(
                        claim_id=_claim_id(source, sentence),
                        claim_text=sentence,
                        source=source,
                        claim_type=claim_type,
                        risk_level=risk_level,
                        verification_required=verification_required,
                    )
                )
        return _dedupe(claims)


def _collect_text(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        texts: list[str] = []
        for key, item in value.items():
            if key in {"answer", "final_answer", "reason", "recommended_fix", "root_cause", "claim", "claim_text"}:
                texts.extend(_collect_text(item))
            elif isinstance(item, (dict, list)):
                texts.extend(_collect_text(item))
        return texts
    if isinstance(value, list):
        texts: list[str] = []
        for item in value:
            texts.extend(_collect_text(item))
        return texts
    return []


def _claim_type(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["should", "recommend", "next action"]):
        return "recommendation"
    if any(word in lowered for word in ["assume", "assumption"]):
        return "assumption"
    if any(word in lowered for word in ["guardian", "governance", "approval"]):
        return "governance"
    if any(word in lowered for word in ["policy", "provider", "permission"]):
        return "policy"
    if any(word in lowered for word in ["security", "credential", "secret", "token"]):
        return "security"
    if any(word in lowered for word in ["architecture", "interface", "schema", "layer"]):
        return "architecture"
    if any(word in lowered for word in ["will", "likely", "trend"]):
        return "prediction"
    return "fact"


def _risk_level(text: str, claim_type: str) -> str:
    lowered = text.lower()
    if claim_type in {"security", "governance"} or any(word in lowered for word in ["secret", "credential", "guardian", "deploy", "permission"]):
        return "high"
    if claim_type in {"policy", "architecture", "prediction"}:
        return "medium"
    return "low"


def _claim_id(source: str, text: str) -> str:
    digest = hashlib.sha256(f"{source}:{text}".encode("utf-8")).hexdigest()[:16]
    return f"claim-{digest}"


def _dedupe(claims: list[Claim]) -> list[Claim]:
    seen: set[str] = set()
    unique: list[Claim] = []
    for claim in claims:
        if claim.claim_id in seen:
            continue
        seen.add(claim.claim_id)
        unique.append(claim)
    return unique
