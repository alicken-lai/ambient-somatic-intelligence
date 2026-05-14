"""
Skill Registry — Discovery, registration, and lifecycle management of skills.

The registry is the central authority for all skills in the system:
  - Register / deregister skills with schema validation
  - Find the best skill for a task (ranked by confidence)
  - List, filter, and query skills by tags
  - Thread-safe access for concurrent use
  - JSONL persistence for state recovery
"""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any

from skills.core.skill_schema import SkillSchema
from skills.core.skill_validator import SkillValidator, ValidationResult

logger = logging.getLogger(__name__)

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
DEFAULT_REGISTRY_PATH = AMBIENT_ROOT / "state" / "skills" / "registry.jsonl"


class SkillRegistry:
    """
    Central registry for all skills in the Ambient OS skill layer.

    Thread-safe. Validates every skill before registration.
    Persists registry metadata to JSONL for recovery.

    Usage:
        registry = SkillRegistry()
        skill_id = registry.register(my_skill)
        matches = registry.find_best("explain anomaly", context={})
        registry.save()
    """

    def __init__(
        self,
        store_path: Path | str | None = None,
        validator: SkillValidator | None = None,
    ):
        self._skills: dict[str, SkillSchema] = {}
        self._tag_index: dict[str, list[str]] = {}
        self._lock = threading.Lock()
        self._validator = validator or SkillValidator()
        self._store_path = Path(store_path) if store_path else DEFAULT_REGISTRY_PATH
        self._deregistered: dict[str, SkillSchema] = {}

    def register(self, skill: SkillSchema) -> str:
        """
        Register a skill after validation.

        Returns the skill_id on success.
        Raises ValueError if validation fails.
        """
        validation = self.validate_before_register(skill)
        if not validation.valid:
            raise ValueError(
                f"Skill '{skill.name}' failed validation: {validation.errors}"
            )

        with self._lock:
            self._skills[skill.skill_id] = skill
            for tag in skill.metadata.tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = []
                if skill.skill_id not in self._tag_index[tag]:
                    self._tag_index[tag].append(skill.skill_id)

        logger.info(
            "Registered skill '%s' v%s (id=%s, governance=%s)",
            skill.name, skill.version, skill.skill_id, skill.governance_level,
        )
        return skill.skill_id

    def deregister(self, skill_id: str) -> bool:
        """
        Remove a skill from the active registry.

        The skill is kept in a deregistered pool for potential re-registration.
        Returns True if the skill was found and removed.
        """
        with self._lock:
            skill = self._skills.pop(skill_id, None)
            if skill is None:
                return False
            self._deregistered[skill_id] = skill
            for tag in skill.metadata.tags:
                ids = self._tag_index.get(tag, [])
                if skill_id in ids:
                    ids.remove(skill_id)
        logger.info("Deregistered skill '%s' (id=%s)", skill.name, skill_id)
        return True

    def get(self, skill_id: str) -> SkillSchema | None:
        """Retrieve a skill by its ID."""
        with self._lock:
            return self._skills.get(skill_id)

    def find_best(
        self, task_description: str, context: dict[str, Any] | None = None,
    ) -> list[tuple[SkillSchema, float]]:
        """
        Find skills matching a task description, ranked by confidence.

        Returns a list of (SkillSchema, confidence_score) tuples sorted
        descending by score.
        """
        context = context or {}
        candidates: list[tuple[SkillSchema, float]] = []

        with self._lock:
            skills = list(self._skills.values())

        for skill in skills:
            if not skill.enabled:
                continue
            score = skill.matches_task(task_description)
            if score > 0:
                candidates.append((skill, score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates

    def find_by_tag(self, tags: list[str]) -> list[SkillSchema]:
        """Find all skills matching any of the given tags."""
        with self._lock:
            matched_ids: set[str] = set()
            for tag in tags:
                matched_ids.update(self._tag_index.get(tag, []))
            return [
                self._skills[sid]
                for sid in matched_ids
                if sid in self._skills and self._skills[sid].enabled
            ]

    def list_all(self) -> list[SkillSchema]:
        """List all registered skills."""
        with self._lock:
            return list(self._skills.values())

    def validate_before_register(self, skill: SkillSchema) -> ValidationResult:
        """Run full schema validation before registration."""
        return self._validator.validate_schema(skill)

    def save(self, path: Path | str | None = None) -> int:
        """
        Persist registry state to JSONL.

        Returns the number of skills saved.
        """
        target = Path(path) if path else self._store_path
        target.parent.mkdir(parents=True, exist_ok=True)

        with self._lock:
            skills = list(self._skills.values())

        try:
            with target.open("w", encoding="utf-8") as f:
                for skill in skills:
                    f.write(json.dumps(skill.to_dict(), ensure_ascii=False) + "\n")
            logger.debug("Saved %d skills to %s", len(skills), target)
            return len(skills)
        except OSError as exc:
            logger.error("Failed to save registry: %s", exc)
            return 0

    def load(self, path: Path | str | None = None) -> int:
        """
        Load registry metadata from JSONL.

        Note: only metadata is loaded — execute callables must be
        re-registered by the skill modules themselves. This method
        returns the number of records read (for audit purposes).
        """
        target = Path(path) if path else self._store_path
        if not target.exists():
            return 0

        count = 0
        try:
            with target.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        json.loads(line)
                        count += 1
                    except json.JSONDecodeError:
                        continue
            logger.debug("Read %d skill records from %s", count, target)
        except OSError as exc:
            logger.warning("Failed to load registry: %s", exc)
        return count

    def status_report(self) -> dict[str, Any]:
        """Summary of the registry state."""
        with self._lock:
            skills = list(self._skills.values())

        by_governance: dict[str, int] = {}
        by_category: dict[str, int] = {}
        for skill in skills:
            by_governance[skill.governance_level] = (
                by_governance.get(skill.governance_level, 0) + 1
            )
            cat = skill.metadata.category
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "total_skills": len(skills),
            "enabled": sum(1 for s in skills if s.enabled),
            "disabled": sum(1 for s in skills if not s.enabled),
            "deregistered": len(self._deregistered),
            "by_governance": by_governance,
            "by_category": by_category,
            "tags": sorted(self._tag_index.keys()),
        }
