"""Build-time import surface for the package-local RAG bootstrap."""

from .templates.runtime.obvious_one_runtime.cache import CacheLock, ensure_cached_object
from .templates.runtime.obvious_one_runtime.paths import RuntimePaths, resolve_runtime_paths

__all__ = [
    "CacheLock",
    "RuntimePaths",
    "ensure_cached_object",
    "resolve_runtime_paths",
]
