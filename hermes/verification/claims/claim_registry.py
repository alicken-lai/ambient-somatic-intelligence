"""Persistent claim registry."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

from hermes.verification.claims.claim_models import Claim, ClaimRecord


class ClaimRegistry:
    def __init__(self, path: str | Path = "reports/claim_registry.json"):
        self.path = Path(path)

    def load(self) -> dict[str, ClaimRecord]:
        if not self.path.is_file():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return {key: ClaimRecord.from_dict(value) for key, value in raw.items()}

    def save(self, records: dict[str, ClaimRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({k: v.to_dict() for k, v in records.items()}, indent=2, ensure_ascii=False), encoding="utf-8")

    def register(self, claims: list[Claim]) -> dict[str, ClaimRecord]:
        records = self.load()
        for claim in claims:
            records.setdefault(claim.claim_id, ClaimRecord(claim_id=claim.claim_id))
        self.save(records)
        return records

    def update_status(self, claim_id: str, status: str, evidence_ids: list[str] | None = None, challenge: str | None = None) -> ClaimRecord:
        records = self.load()
        current = records.get(claim_id, ClaimRecord(claim_id=claim_id))
        record = ClaimRecord(
            claim_id=claim_id,
            status=status,
            evidence=list(dict.fromkeys([*current.evidence, *(evidence_ids or [])])),
            last_checked=datetime.now(timezone.utc).isoformat(),
            verification_count=current.verification_count + 1,
            challenge_history=[*current.challenge_history, *([challenge] if challenge else [])],
        )
        records[claim_id] = record
        self.save(records)
        return record
