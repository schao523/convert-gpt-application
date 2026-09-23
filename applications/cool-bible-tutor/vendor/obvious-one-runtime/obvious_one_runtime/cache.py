"""Race-safe content-addressed cache activation."""

from __future__ import annotations

from collections.abc import Callable
import json
import os
from pathlib import Path
import shutil
import stat
import time
import uuid


COMPLETION_FILE = ".obvious-one-complete.json"


def _remove_tree(path: Path) -> None:
    if not path.exists():
        return
    def retry(function, value, _error):
        os.chmod(value, stat.S_IWRITE)
        function(value)
    shutil.rmtree(path, onerror=retry)


class CacheLock:
    def __init__(self, target: Path, timeout_seconds: float = 120.0) -> None:
        self.path = target.with_name(target.name + ".lock")
        self.timeout_seconds = timeout_seconds
        self._descriptor: int | None = None

    def __enter__(self) -> "CacheLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            try:
                self._descriptor = os.open(
                    self.path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    0o600,
                )
                os.write(self._descriptor, str(os.getpid()).encode("ascii"))
                return self
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"cache_lock_timeout: {self.path}")
                time.sleep(0.02)

    def __exit__(self, _type, _value, _traceback) -> None:
        if self._descriptor is not None:
            os.close(self._descriptor)
            self._descriptor = None
        self.path.unlink(missing_ok=True)


def _is_complete(target: Path, digest: str) -> bool:
    marker = target / COMPLETION_FILE
    if not marker.is_file():
        return False
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return data == {"digest": digest, "schema_version": 1}


def ensure_cached_object(
    target: Path,
    digest: str,
    populate: Callable[[Path], None],
    verify: Callable[[Path], None],
) -> Path:
    # ``Path.resolve()`` can switch to a ``\\?\``-prefixed spelling on Windows
    # after another thread creates the target. Preserve one stable lexical
    # absolute spelling across both sides of that race.
    target = Path(os.path.abspath(os.fspath(target)))
    if _is_complete(target, digest):
        verify(target)
        return target
    with CacheLock(target):
        if _is_complete(target, digest):
            verify(target)
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        stage = target.with_name(f".{target.name}.stage-{uuid.uuid4().hex}")
        backup = target.with_name(f".{target.name}.previous")
        _remove_tree(stage)
        stage.mkdir()
        try:
            populate(stage)
            verify(stage)
            (stage / COMPLETION_FILE).write_text(
                json.dumps(
                    {"digest": digest, "schema_version": 1},
                    indent=2,
                    sort_keys=True,
                ) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            _remove_tree(backup)
            if target.exists():
                os.replace(target, backup)
            try:
                os.replace(stage, target)
            except Exception:
                if backup.exists() and not target.exists():
                    os.replace(backup, target)
                raise
            _remove_tree(backup)
        finally:
            _remove_tree(stage)
        return target
