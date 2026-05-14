"""
Orchestration Templates — Store and retrieve reusable orchestration templates
extracted from successful execution patterns.

Templates capture the task sequence, agent requirements, and success metrics
of proven workflows, allowing the system to propose known-good execution plans
for similar future tasks.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from memory.evolution.pattern_miner import SuccessPattern

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationTemplate:
    """A reusable orchestration template derived from successful patterns."""
    template_id: str
    name: str
    description: str
    task_sequence: list[dict[str, Any]]
    agent_requirements: list[str]
    estimated_duration: float
    success_rate: float
    created_from: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    usage_count: int = 0
    last_used: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "task_sequence": self.task_sequence,
            "agent_requirements": self.agent_requirements,
            "estimated_duration": round(self.estimated_duration, 1),
            "success_rate": round(self.success_rate, 3),
            "created_from": self.created_from,
            "created_at": self.created_at,
            "usage_count": self.usage_count,
            "last_used": self.last_used,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "OrchestrationTemplate":
        return OrchestrationTemplate(
            template_id=data.get("template_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            task_sequence=data.get("task_sequence", []),
            agent_requirements=data.get("agent_requirements", []),
            estimated_duration=data.get("estimated_duration", 0),
            success_rate=data.get("success_rate", 0),
            created_from=data.get("created_from", ""),
            created_at=data.get("created_at", ""),
            usage_count=data.get("usage_count", 0),
            last_used=data.get("last_used"),
        )


class OrchestrationTemplateStore:
    """
    Store and retrieve reusable orchestration templates.

    Templates are persisted as JSONL and can be queried by similarity
    to find matching workflows for new tasks.

    Usage:
        store = OrchestrationTemplateStore()
        template = store.extract_template(success_pattern)
        store.store(template)
        matches = store.find("deploy backend service")
        report = store.effectiveness_report()
    """

    def __init__(self, store_path: Path | str | None = None):
        if store_path is None:
            root = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
            self._store_path = root / "memory" / "evolution" / "templates.jsonl"
        else:
            self._store_path = Path(store_path)

        self._templates: list[OrchestrationTemplate] = []
        self._load()

    def extract_template(self, success_pattern: SuccessPattern) -> OrchestrationTemplate:
        """
        Create an OrchestrationTemplate from a successful execution pattern.

        Extracts the key characteristics of the pattern into a reusable template
        that can guide future task planning.
        """
        task_sequence = self._infer_task_sequence(success_pattern)

        template = OrchestrationTemplate(
            template_id=f"tmpl-{uuid.uuid4().hex[:8]}",
            name=self._generate_template_name(success_pattern),
            description=success_pattern.description,
            task_sequence=task_sequence,
            agent_requirements=success_pattern.agents_involved[:],
            estimated_duration=success_pattern.avg_duration,
            success_rate=success_pattern.success_rate,
            created_from=success_pattern.pattern_id,
        )

        logger.info("Extracted template '%s' from pattern %s",
                    template.name, success_pattern.pattern_id)
        return template

    def store(self, template: OrchestrationTemplate) -> None:
        """Save a template to the persistent store."""
        self._templates.append(template)
        self._persist()
        logger.debug("Stored template '%s'", template.template_id)

    def find(self, query: str, max_results: int = 5) -> list[OrchestrationTemplate]:
        """
        Find templates matching a query by token overlap similarity.

        Returns templates ranked by relevance to the query.
        """
        if not self._templates:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return self._templates[:max_results]

        scored: list[tuple[float, OrchestrationTemplate]] = []
        for template in self._templates:
            template_tokens = self._tokenize(
                f"{template.name} {template.description}"
            )
            if not template_tokens:
                continue

            overlap = len(query_tokens & template_tokens)
            score = overlap / max(len(query_tokens), 1)

            if template.success_rate > 0.8:
                score *= 1.1
            if template.usage_count > 0:
                score *= 1.0 + min(template.usage_count / 10.0, 0.5)

            scored.append((score, template))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:max_results] if _ > 0]

    def list_all(self) -> list[OrchestrationTemplate]:
        """List all stored templates."""
        return list(self._templates)

    def effectiveness_report(self) -> dict[str, Any]:
        """Generate a report on template usage and effectiveness."""
        if not self._templates:
            return {
                "total_templates": 0,
                "templates": [],
                "avg_success_rate": 0,
                "most_used": None,
                "highest_success_rate": None,
            }

        total = len(self._templates)
        avg_success = sum(t.success_rate for t in self._templates) / total
        most_used = max(self._templates, key=lambda t: t.usage_count)
        highest_sr = max(self._templates, key=lambda t: t.success_rate)

        templates_summary = [
            {
                "template_id": t.template_id,
                "name": t.name,
                "usage_count": t.usage_count,
                "success_rate": round(t.success_rate, 3),
                "estimated_duration": round(t.estimated_duration, 1),
            }
            for t in sorted(self._templates, key=lambda t: t.usage_count, reverse=True)
        ]

        return {
            "total_templates": total,
            "templates": templates_summary,
            "avg_success_rate": round(avg_success, 3),
            "most_used": {
                "template_id": most_used.template_id,
                "name": most_used.name,
                "usage_count": most_used.usage_count,
            },
            "highest_success_rate": {
                "template_id": highest_sr.template_id,
                "name": highest_sr.name,
                "success_rate": round(highest_sr.success_rate, 3),
            },
        }

    def record_usage(self, template_id: str) -> bool:
        """Record that a template was used."""
        for template in self._templates:
            if template.template_id == template_id:
                template.usage_count += 1
                template.last_used = datetime.now(timezone.utc).isoformat()
                self._persist()
                return True
        return False

    def _infer_task_sequence(self, pattern: SuccessPattern) -> list[dict[str, Any]]:
        """Infer a task sequence from a success pattern."""
        description = pattern.description.lower()
        steps: list[dict[str, Any]] = []

        if "strategy" in description:
            strategy_name = description.replace("strategy '", "").replace("' succeeds consistently", "")
            steps.append({
                "step": 1,
                "action": "apply_strategy",
                "strategy": strategy_name,
                "parallel": False,
            })
        elif "task type" in description:
            task_type = description.replace("task type '", "").replace("' has high success rate", "")
            steps.append({
                "step": 1,
                "action": "execute_task",
                "task_type": task_type,
                "parallel": True,
            })
        else:
            steps.append({
                "step": 1,
                "action": "execute",
                "description": pattern.description,
                "parallel": False,
            })

        if pattern.agents_involved:
            steps.append({
                "step": len(steps) + 1,
                "action": "verify_result",
                "agents": pattern.agents_involved,
                "parallel": False,
            })

        return steps

    def _generate_template_name(self, pattern: SuccessPattern) -> str:
        """Generate a concise template name from a pattern."""
        desc = pattern.description
        desc = desc.replace("Strategy '", "").replace("' succeeds consistently", "")
        desc = desc.replace("Task type '", "").replace("' has high success rate", "")
        words = desc.split()[:4]
        return "_".join(w.lower() for w in words if w.isalnum())

    def _tokenize(self, text: str) -> set[str]:
        """Tokenize text for similarity matching."""
        tokens = re.findall(r"[a-z0-9\u4e00-\u9fff]{2,}", text.lower())
        stop_words = {"the", "and", "for", "with", "this", "that", "from"}
        return {t for t in tokens if t not in stop_words}

    def _load(self) -> None:
        """Load templates from JSONL store."""
        if not self._store_path.exists():
            return
        try:
            with self._store_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        self._templates.append(OrchestrationTemplate.from_dict(data))
                    except (json.JSONDecodeError, KeyError):
                        continue
        except OSError as e:
            logger.warning("Failed to load templates: %s", e)

    def _persist(self) -> None:
        """Persist all templates to JSONL store."""
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._store_path.open("w", encoding="utf-8") as f:
                for template in self._templates:
                    f.write(json.dumps(template.to_dict(), ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning("Failed to persist templates: %s", e)
