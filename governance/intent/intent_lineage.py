"""Intent lineage — trace motivational ancestry."""

from __future__ import annotations

from governance.intent.constitutional_intent_lineage import ConstitutionalIntentLineage


class IntentLineage:
    def __init__(self) -> None:
        self._lineage = ConstitutionalIntentLineage()

    def trace(self, text: str, *, intent_id: str = "current"):
        return self._lineage.trace(text, intent_id=intent_id)
