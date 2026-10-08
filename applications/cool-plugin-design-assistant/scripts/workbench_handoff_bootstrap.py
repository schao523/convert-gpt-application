"""Resolve the shared Workbench handoff runtime for source and release trees."""

from __future__ import annotations

import importlib
from pathlib import Path
import sys
from types import ModuleType


def _load_runtime(package_name: str) -> ModuleType:
    scripts = Path(__file__).resolve().parent
    vendor = scripts / "vendor"
    if (vendor / "obvious_one_plugin_framework" / package_name).is_dir():
        sys.path.insert(0, str(vendor))
        return importlib.import_module(f"obvious_one_plugin_framework.{package_name}")

    for parent in Path(__file__).resolve().parents:
        source = parent / "src"
        if (source / "obvious_one_plugin_framework" / package_name).is_dir():
            sys.path.insert(0, str(source))
            return importlib.import_module(f"obvious_one_plugin_framework.{package_name}")
    raise RuntimeError(f"{package_name}_runtime_unavailable")


def load_workbench_handoff() -> ModuleType:
    return _load_runtime("workbench_handoff")


def load_plugin_authoring() -> ModuleType:
    return _load_runtime("plugin_authoring")


__all__ = ["load_plugin_authoring", "load_workbench_handoff"]
