"""Interoperability provenance chain — links treaties to foreign records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.civilization.foreign_identity_record import ForeignIdentityRecord
from governance.civilization.provenance_exchange import ProvenanceExchange
from governance.civilization.treaty_record import TreatyRecord


@dataclass
class InteroperabilityProvenance:
    chain_id: str
    treaty: dict[str, Any]
    foreign_identity: dict[str, Any]
    exchange: dict[str, Any]
    intact: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "treaty": self.treaty,
            "foreign_identity": self.foreign_identity,
            "exchange": self.exchange,
            "intact": self.intact,
        }


def build_interop_chain(
    treaty: TreatyRecord,
    *,
    provenance_payload: dict[str, Any] | None = None,
) -> InteroperabilityProvenance:
    foreign = ForeignIdentityRecord.from_sovereign(treaty.sovereign_b)
    exchange = ProvenanceExchange().validate(
        provenance_payload or {"source": treaty.sovereign_a, "route_name": "civilization_interop"},
        sovereign_id=treaty.sovereign_b,
    )
    intact = exchange.exchange_valid and treaty.guardian_supremacy
    return InteroperabilityProvenance(
        chain_id=f"chain-{treaty.treaty_id}",
        treaty=treaty.to_dict(),
        foreign_identity=foreign.to_dict(),
        exchange=exchange.to_dict(),
        intact=intact,
    )
