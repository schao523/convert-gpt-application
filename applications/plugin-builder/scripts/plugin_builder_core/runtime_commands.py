"""Explicit, evidence-producing direct command resolution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import sys
from typing import Callable


@dataclass(frozen=True)
class CommandResolution:
    declared_argv: tuple[str, ...]
    observed_argv: tuple[str, ...] | None
    adapter: str | None
    diagnostic: str | None


def resolve_direct_argv(
    argv: list[str],
    candidate: Path,
    *,
    executable_lookup: Callable[[str], str | None] = shutil.which,
) -> CommandResolution:
    del candidate
    declared = tuple(argv)
    if not declared:
        return CommandResolution(declared, None, None, "argv_missing")
    unknown = next(
        (item for item in declared if item.startswith("{") and item.endswith("}") and item != "{python}"),
        None,
    )
    if unknown is not None:
        return CommandResolution(declared, None, None, "adapter_token_unsupported")
    if declared[0] == "{python}":
        return CommandResolution(declared, (sys.executable, *declared[1:]), "CURRENT_PYTHON", None)
    executable = executable_lookup(declared[0])
    if executable is None:
        return CommandResolution(declared, None, None, "executable_unavailable")
    return CommandResolution(declared, (str(Path(executable).resolve()), *declared[1:]), None, None)


__all__ = ["CommandResolution", "resolve_direct_argv"]
