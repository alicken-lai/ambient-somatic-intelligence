"""Persistent skill registry."""

from __future__ import annotations

from pathlib import Path
import json

from hermes.deliberation.skills.skill_models import DeliberationSkill


class SkillRegistry:
    def __init__(self, path: str | Path = "reports/deliberation_skill_registry.json"):
        self.path = Path(path)

    def load(self) -> dict[str, DeliberationSkill]:
        if not self.path.is_file():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return {key: DeliberationSkill.from_dict(value) for key, value in raw.items()}

    def save(self, skills: dict[str, DeliberationSkill]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {key: value.to_dict() for key, value in skills.items()}
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def upsert_many(self, skills: list[DeliberationSkill]) -> dict[str, DeliberationSkill]:
        current = self.load()
        for skill in skills:
            current[skill.skill_id] = skill
        self.save(current)
        return current
