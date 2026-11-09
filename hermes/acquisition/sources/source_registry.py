"""Persistent evidence source registry."""

from __future__ import annotations

from pathlib import Path
import json

from hermes.acquisition.sources.source_models import EvidenceSource


class SourceRegistry:
    def __init__(self, path: str | Path = "reports/evidence_source_registry.json"):
        self.path = Path(path)

    def load(self) -> dict[str, EvidenceSource]:
        if not self.path.is_file():
            return default_sources()
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return {key: EvidenceSource.from_dict(value) for key, value in raw.items()}

    def save(self, sources: dict[str, EvidenceSource]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({k: v.to_dict() for k, v in sources.items()}, indent=2, ensure_ascii=False), encoding="utf-8")

    def enabled_sources(self) -> list[EvidenceSource]:
        return [source for source in self.load().values() if source.enabled]


def default_sources() -> dict[str, EvidenceSource]:
    sources = [
        EvidenceSource("dmn", "DMN", 0.75, metadata={"path": "memory/dmn.jsonl"}),
        EvidenceSource("reports", "Reports", 0.85, metadata={"paths": ["reports/*.md", "reports/*.json"]}),
        EvidenceSource("benchmarks", "Benchmarks", 0.8, metadata={"path": "tests/golden_traces/benchmarks.json"}),
        EvidenceSource("tests", "Tests", 0.9, metadata={"path": "tests"}),
        EvidenceSource("guardian_logs", "Guardian Logs", 0.95, metadata={"paths": ["logs/actions.jsonl", "logs/checksums.jsonl"]}),
        EvidenceSource("provider_reports", "Provider Reports", 0.7, metadata={"paths": ["reports/*provider*"]}),
        EvidenceSource("playbooks", "Playbooks", 0.8, metadata={"path": "reports/playbook_report.md"}),
        EvidenceSource("skills", "Skills", 0.78, metadata={"path": "reports/skill_report.md"}),
        EvidenceSource("failure_reports", "Failure Reports", 0.82, metadata={"path": "reports/failure_learning_report.md"}),
        EvidenceSource("verification_reports", "Verification Reports", 0.88, metadata={"paths": ["reports/evidence_report.md", "reports/verification_report.md"]}),
        EvidenceSource("future_external", "Future external sources", 0.0, enabled=False),
    ]
    return {source.source_id: source for source in sources}
