"""Area 4: Phase 3 provenance and lineage."""

from governance.temporal.epoch_lineage import EpochLineage, EpochLineageNode
from governance.temporal.historical_trace_record import HistoricalTraceRecord
from governance.temporal.temporal_provenance import TemporalProvenance


def test_temporal_provenance() -> None:
    tp = TemporalProvenance()
    assert tp.validate({"epoch_id": "e1"}).provenance_valid
    assert not tp.validate({"autonomous_rewrite": True}).provenance_valid


def test_epoch_lineage_valid() -> None:
    nodes = [
        EpochLineageNode("e1", parent_epoch_id=None, depth=0),
        EpochLineageNode("e2", parent_epoch_id="e1", depth=1),
    ]
    v = EpochLineage().validate_chain(nodes)
    assert v.lineage_valid


def test_historical_trace_record() -> None:
    tr = HistoricalTraceRecord.create(
        epoch_id="e1", runtime_id="ambient", claim="advisory trace"
    )
    assert tr.to_dict()["advisory_only"] is True
