"""Explicit, hash-bound member decisions for safe plugin updates."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath

from .implementation_plan import canonical_bytes, write_bytes_transactionally


@dataclass(frozen=True)
class UpdateDecisionOutcome:
    status: str
    errors: tuple[str, ...]
    member: str | None = None
    decision: str | None = None


def _safe_member(value: str) -> bool:
    if not value or "\\" in value or value.startswith("/"):
        return False
    parts = value.split("/")
    return not any(part in {"", ".", ".."} for part in parts) and ":" not in parts[0] and PurePosixPath(value).as_posix() == value


def resolve_update_member(
    session_path: Path,
    member: str,
    decision: str,
    evidence: str,
) -> UpdateDecisionOutcome:
    if decision not in {"keep", "replace", "remove"}:
        return UpdateDecisionOutcome("FAIL", ("update.decision_invalid",))
    if not _safe_member(member):
        return UpdateDecisionOutcome("FAIL", ("update.member_invalid",))
    if not evidence.strip():
        return UpdateDecisionOutcome("FAIL", ("update.evidence_required",))
    path = Path(session_path)
    try:
        session = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return UpdateDecisionOutcome("FAIL", ("update.session_invalid",))
    if not isinstance(session, dict) or session.get("schema_version") != 2 or session.get("operation") != "update":
        return UpdateDecisionOutcome("FAIL", ("update.session_required",))
    baseline = path.parent / str((session.get("baseline") or {}).get("path", ""))
    target = baseline.joinpath(*PurePosixPath(member).parts)
    if not target.is_file():
        return UpdateDecisionOutcome("FAIL", ("update.member_not_in_baseline",))
    decisions_path = path.parent / "update-decisions.json"
    decisions: dict[str, object] = {
        "schema": "plugin-builder-update-decisions-v1",
        "baseline_sha256": (session.get("baseline") or {}).get("sha256"),
        "members": [],
    }
    if decisions_path.is_file():
        try:
            loaded = json.loads(decisions_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                decisions = loaded
        except (OSError, UnicodeError, json.JSONDecodeError):
            return UpdateDecisionOutcome("FAIL", ("update.decisions_invalid",))
    by_member = {
        item["member"]: item for item in decisions.get("members", [])
        if isinstance(item, dict) and isinstance(item.get("member"), str)
    }
    by_member[member] = {"decision": decision, "evidence": evidence.strip(), "member": member}
    decisions["schema"] = "plugin-builder-update-decisions-v1"
    decisions["baseline_sha256"] = (session.get("baseline") or {}).get("sha256")
    decisions["members"] = [by_member[key] for key in sorted(by_member)]
    write_bytes_transactionally(decisions_path, canonical_bytes(decisions))
    return UpdateDecisionOutcome("PASS", (), member, decision)
