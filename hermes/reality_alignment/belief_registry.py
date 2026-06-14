"""Persistent belief registry."""

from __future__ import annotations

import json
from pathlib import Path

from hermes.reality_alignment.reality_models import Belief, RealityTarget


class BeliefRegistry:
    def __init__(self, path: str | Path = "reports/belief_registry.json"):
        self.path = Path(path)

    def load(self) -> dict[str, Belief]:
        if not self.path.is_file():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return {key: Belief.from_dict(value) for key, value in raw.items()}

    def save(self, beliefs: dict[str, Belief]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({key: value.to_dict() for key, value in beliefs.items()}, indent=2, ensure_ascii=False), encoding="utf-8")

    def upsert_many(self, beliefs: list[Belief]) -> dict[str, Belief]:
        current = self.load()
        for belief in beliefs:
            current[belief.belief_id] = belief
        self.save(current)
        return current

    def seed_from_targets(self, targets: list[RealityTarget], scores: dict[str, dict]) -> dict[str, Belief]:
        beliefs = []
        current = self.load()
        for target in targets:
            belief_id = f"belief:{target.target_id}"
            previous = current.get(belief_id)
            beliefs.append(
                Belief(
                    belief_id=belief_id,
                    statement=target.statement,
                    confidence=target.confidence,
                    reality_score=float(scores.get(target.target_id, {}).get("reality_score", 0.0)),
                    challenge_count=previous.challenge_count if previous else 0,
                    status=previous.status if previous else "active",
                    source_target_id=target.target_id,
                )
            )
        return self.upsert_many(beliefs)
