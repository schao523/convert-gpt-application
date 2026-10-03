"""Resolve the shared Workbench handoff runtime for source and release trees."""

from __future__ import annotations

import importlib
from pathlib import Path
import sys
from types import ModuleType


def load_workbench_handoff() -> ModuleType:
    scripts = Path(__file__).resolve().parent
    vendor = scripts / "vendor"
    if (vendor / "obvious_one_plugin_framework" / "workbench_handoff").is_dir():
        sys.path.insert(0, str(vendor))
        return importlib.import_module("obvious_one_plugin_framework.workbench_handoff")

    for parent in Path(__file__).resolve().parents:
        source = parent / "src"
        if (source / "obvious_one_plugin_framework" / "workbench_handoff").is_dir():
            sys.path.insert(0, str(source))
            return importlib.import_module("obvious_one_plugin_framework.workbench_handoff")
    raise RuntimeError("workbench_handoff_runtime_unavailable")


__all__ = ["load_workbench_handoff"]
