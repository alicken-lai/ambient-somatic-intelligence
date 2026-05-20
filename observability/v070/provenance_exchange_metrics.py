"""Provenance exchange metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.civilization.provenance_exchange import ProvenanceExchange

_VALID = {"source": "foreign-peer", "route_name": "civilization_interop"}
_INVALID = {"merge_identity": True}


@dataclass
class ProvenanceExchangeMetrics:
    exchange_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"exchange_rate": round(self.exchange_rate, 4)}


def collect_provenance_exchange_metrics() -> ProvenanceExchangeMetrics:
    ex = ProvenanceExchange()
    passed = 0
    if ex.validate(_VALID).exchange_valid:
        passed += 1
    if not ex.validate(_INVALID).exchange_valid:
        passed += 1
    return ProvenanceExchangeMetrics(exchange_rate=passed / 2)
