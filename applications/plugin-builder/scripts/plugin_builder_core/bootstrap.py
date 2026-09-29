"""Resolve the bundled authoring runtime, with a development-checkout fallback."""

from __future__ import annotations

import importlib
from pathlib import Path
import sys
from types import ModuleType


def load_plugin_authoring() -> ModuleType:
    scripts_root = Path(__file__).resolve().parents[1]
    vendor = scripts_root / "vendor"
    if (vendor / "obvious_one_plugin_framework" / "plugin_authoring").is_dir():
        sys.path.insert(0, str(vendor))
        return importlib.import_module("obvious_one_plugin_framework.plugin_authoring")

    for parent in Path(__file__).resolve().parents:
        source = parent / "src"
        if (source / "obvious_one_plugin_framework" / "plugin_authoring").is_dir():
            sys.path.insert(0, str(source))
            return importlib.import_module("obvious_one_plugin_framework.plugin_authoring")
    raise RuntimeError("plugin_authoring_runtime_unavailable")


plugin_authoring = load_plugin_authoring()
