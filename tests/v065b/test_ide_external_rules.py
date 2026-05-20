"""Area 4: IDE external rule exports."""

from pathlib import Path

from governance.external.external_rule_boundary import ADVISORY_HEADER

RULES = Path(__file__).resolve().parents[2] / "hermes" / "rules" / "external"


def test_all_exports_have_advisory_header() -> None:
    for name in (
        "cursor_external_rules.md",
        "vscode_external_rules.md",
        "codex_external_rules.md",
        "antigravity_external_rules.md",
    ):
        text = (RULES / name).read_text(encoding="utf-8")
        assert ADVISORY_HEADER in text
