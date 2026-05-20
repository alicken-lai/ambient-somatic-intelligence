"""Value lineage — trace normative ancestry."""

from __future__ import annotations

from governance.value.constitutional_lineage import ConstitutionalLineage


class ValueLineage:
    def __init__(self) -> None:
        self._lineage = ConstitutionalLineage()

    def trace(self, text: str, *, value_id: str = "current"):
        return self._lineage.trace(text, value_id=value_id)
