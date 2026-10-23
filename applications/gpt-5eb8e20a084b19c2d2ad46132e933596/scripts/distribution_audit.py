"""Static audit hook for immutable imported plugin content."""
from __future__ import annotations

from pathlib import Path


def audit_distribution(stage: Path, contract: object) -> tuple[str, ...]:
    issues = []
    root = Path(stage)
    if not (root / "plugin.json").is_file():
        issues.append("missing plugin.json")
    if not (root / ".codex-plugin" / "plugin.json").is_file():
        issues.append("missing .codex-plugin/plugin.json")
    return tuple(issues)
