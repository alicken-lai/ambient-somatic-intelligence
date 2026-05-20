"""Area 4: Provenance exchange and interop chain."""

from governance.civilization.interoperability_provenance import build_interop_chain
from governance.civilization.provenance_exchange import ProvenanceExchange
from governance.civilization.treaty_record import TreatyRecord


def test_valid_provenance_exchange() -> None:
    v = ProvenanceExchange().validate(
        {"source": "foreign", "route_name": "civilization_interop"}
    )
    assert v.exchange_valid is True


def test_interop_chain_intact() -> None:
    treaty = TreatyRecord.create("foreign-a", "ambient")
    chain = build_interop_chain(
        treaty,
        provenance_payload={"source": "foreign-a", "route_name": "civilization_interop"},
    )
    assert chain.intact is True
