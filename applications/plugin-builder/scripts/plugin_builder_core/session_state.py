"""Thin, deterministic pause, resume, and cancellation operations."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .implementation_plan import canonical_bytes, write_bytes_transactionally
from .session_contract import validate_session


@dataclass(frozen=True)
class SessionStateOutcome:
    status: str
    errors: tuple[str, ...]
    stage: str | None = None


def _load_session(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def change_session_state(session_path: Path, action: str) -> SessionStateOutcome:
    """Apply one lifecycle action without changing candidate or package artifacts."""

    path = Path(session_path)
    session = _load_session(path)
    if session is None or session.get("schema_version") != 2 or validate_session(session):
        return SessionStateOutcome("FAIL", ("session_state.invalid_session",))

    sidecar = path.parent / "pause-state.json"
    current = session.get("stage")
    if action == "pause":
        if current in {"H1", "E2"}:
            return SessionStateOutcome("BLOCKED", ("session_state.pause_not_allowed",), current)
        write_bytes_transactionally(
            sidecar,
            canonical_bytes({"schema": "plugin-builder-pause-state-v1", "resume_stage": current}),
        )
        session["stage"] = "H1"
    elif action == "resume":
        if current != "H1":
            return SessionStateOutcome("BLOCKED", ("session_state.not_paused",), current)
        pause = _load_session(sidecar)
        resume_stage = pause.get("resume_stage") if isinstance(pause, dict) else None
        if not isinstance(resume_stage, str) or resume_stage in {"H1", "E2"}:
            return SessionStateOutcome("FAIL", ("session_state.pause_record_invalid",), current)
        session["stage"] = resume_stage
    elif action == "cancel":
        session["stage"] = "E2"
    else:
        return SessionStateOutcome("FAIL", ("session_state.unsupported_action",), current)

    write_bytes_transactionally(path, canonical_bytes(session))
    if action in {"resume", "cancel"} and sidecar.exists():
        sidecar.unlink()
    return SessionStateOutcome("PASS", (), session["stage"])
