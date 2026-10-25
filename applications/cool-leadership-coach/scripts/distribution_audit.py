"""Static audit for the reviewed Leadership Coach distribution."""
from __future__ import annotations

from pathlib import Path


def audit_distribution(stage: Path, contract: object) -> tuple[str, ...]:
    required = ("plugin.json", ".codex-plugin/plugin.json", "THIRD_PARTY_NOTICES.md")
    return tuple(f"missing {item}" for item in required if not (Path(stage) / item).is_file())
