"""Validate Plugin Builder session state and approval bindings."""

from __future__ import annotations

from pathlib import PurePosixPath
import re
from typing import Any


OPERATIONS = frozenset({"create", "update"})
STAGES = frozenset(
    {"S0", "S1", "S2", "W1", "S3", "S4", "W2", "S5", "F1", "F2", "F3", "H1", "E1", "E2", "E3"}
)
EVIDENCE_STATES = frozenset({"PASS", "FAIL", "NOT VERIFIED", "NOT APPLICABLE"})
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ROOT_KEYS = {
    "schema_version",
    "operation",
    "stage",
    "workspace_path",
    "approved_spec_sha256",
    "plan_sha256",
    "baseline",
    "w1",
    "candidate",
    "verification",
    "w2",
    "package",
    "requirements",
}


def _mapping(value: object) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _relative_posix(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"):
        return False
    raw_parts = value.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        return False
    if raw_parts[0].endswith(":") or ":" in raw_parts[0]:
        return False
    candidate = PurePosixPath(value)
    return not candidate.is_absolute() and candidate.as_posix() == value


def _approval(value: object, keys: set[str]) -> bool:
    item = _mapping(value)
    return item is not None and set(item) == keys and item.get("approved") is True


def _validate_identity(
    errors: list[str],
    value: object,
    label: str,
    *,
    require_path: bool,
    extra_keys: set[str] = frozenset(),
) -> dict[str, Any] | None:
    item = _mapping(value)
    expected = {"sha256", *extra_keys} | ({"path"} if require_path else set())
    if item is None or set(item) != expected:
        errors.append(f"{label}.invalid_object")
        return item
    if not _sha256(item.get("sha256")):
        errors.append(f"{label}.sha256.invalid")
    if require_path and not _relative_posix(item.get("path")):
        errors.append(f"{label}.path.invalid_relative_posix_path")
    for key in extra_keys:
        if not _sha256(item.get(key)):
            errors.append(f"{label}.{key}.invalid")
    return item


def _validate_requirements(errors: list[str], value: object) -> dict[str, bool]:
    registered: dict[str, bool] = {}
    if not isinstance(value, list):
        errors.append("requirements.invalid_list")
        return registered
    seen: set[str] = set()
    for index, entry in enumerate(value):
        label = f"requirements[{index}]"
        item = _mapping(entry)
        if item is None or set(item) != {"id", "owner", "evidence", "required"}:
            errors.append(f"{label}.invalid_object")
            continue
        requirement_id = item.get("id")
        if not isinstance(requirement_id, str) or not requirement_id:
            errors.append(f"{label}.id.invalid")
        elif requirement_id in seen:
            errors.append(f"requirements.duplicate_id:{requirement_id}")
        else:
            seen.add(requirement_id)
        if not isinstance(item.get("owner"), str) or not item["owner"]:
            errors.append(f"{label}.owner.invalid")
        evidence = item.get("evidence")
        if not isinstance(evidence, str) or evidence not in EVIDENCE_STATES:
            errors.append(f"{label}.evidence.unsupported")
        required = item.get("required")
        if type(required) is not bool:
            errors.append(f"{label}.required.invalid")
        elif isinstance(requirement_id, str) and requirement_id and requirement_id not in registered:
            registered[requirement_id] = required
    return registered


def _validate_verification(
    errors: list[str],
    value: object,
    candidate: dict[str, Any] | None,
    requirements: dict[str, bool],
) -> dict[str, Any] | None:
    item = _mapping(value)
    if item is None or set(item) != {"sha256", "candidate_sha256", "results"}:
        errors.append("verification.invalid_object")
        return item
    if not _sha256(item.get("sha256")):
        errors.append("verification.sha256.invalid")
    if not _sha256(item.get("candidate_sha256")):
        errors.append("verification.candidate_sha256.invalid")
    elif candidate is not None and item["candidate_sha256"] != candidate.get("sha256"):
        errors.append("verification.candidate_sha256_mismatch")
    results = item.get("results")
    if not isinstance(results, list):
        errors.append("verification.results.invalid_list")
        for requirement_id, required in requirements.items():
            if required:
                errors.append(f"verification.missing_required_result:{requirement_id}")
        return item
    seen: set[str] = set()
    for index, entry in enumerate(results):
        label = f"verification.results[{index}]"
        result = _mapping(entry)
        if result is None or set(result) != {"id", "required", "state"}:
            errors.append(f"{label}.invalid_object")
            continue
        result_id = result.get("id")
        if not isinstance(result_id, str) or not result_id:
            errors.append(f"{label}.id.invalid")
        elif result_id in seen:
            errors.append(f"verification.results.duplicate_id:{result_id}")
        else:
            seen.add(result_id)
        required = result.get("required")
        if type(required) is not bool:
            errors.append(f"{label}.required.invalid")
        elif isinstance(result_id, str) and result_id:
            if result_id not in requirements:
                errors.append(f"{label}.unknown_requirement")
            elif required != requirements[result_id]:
                errors.append(f"{label}.required_mismatch")
        state = result.get("state")
        if not isinstance(state, str) or state not in EVIDENCE_STATES:
            errors.append(f"{label}.state.unsupported")
    for requirement_id, required in requirements.items():
        if required and requirement_id not in seen:
            errors.append(f"verification.missing_required_result:{requirement_id}")
    return item


def _has_required_failure(verification: dict[str, Any] | None) -> bool:
    if verification is None or not isinstance(verification.get("results"), list):
        return False
    return any(
        isinstance(result, dict)
        and result.get("required") is True
        and result.get("state") == "FAIL"
        for result in verification["results"]
    )


def validate_session(payload: object) -> list[str]:
    """Return every session contract error in deterministic order."""

    session = _mapping(payload)
    if session is None:
        return ["session.invalid_object"]
    errors: list[str] = []
    for key in sorted(_ROOT_KEYS - set(session)):
        errors.append(f"{key}.required")
    for key in sorted(set(session) - _ROOT_KEYS):
        errors.append(f"session.unknown_key:{key}")

    if session.get("schema_version") != 1:
        errors.append("schema_version.unsupported")
    operation = session.get("operation")
    if not isinstance(operation, str) or operation not in OPERATIONS:
        errors.append("operation.unsupported")
    stage = session.get("stage")
    if not isinstance(stage, str) or stage not in STAGES:
        errors.append("stage.unsupported")
    if not _relative_posix(session.get("workspace_path")):
        errors.append("workspace_path.invalid_relative_posix_path")
    if not _sha256(session.get("approved_spec_sha256")):
        errors.append("approved_spec_sha256.invalid")
    if not _sha256(session.get("plan_sha256")):
        errors.append("plan_sha256.invalid")
    requirements = _validate_requirements(errors, session.get("requirements"))

    baseline = None
    if session.get("operation") == "update" and session.get("baseline") is None:
        errors.append("baseline.required_for_update")
    elif session.get("baseline") is not None:
        baseline = _validate_identity(errors, session["baseline"], "baseline", require_path=True)

    w1 = session.get("w1")
    w1_approved = _approval(w1, {"approved", "plan_sha256"})
    if w1 is not None:
        if not w1_approved or not _sha256(_mapping(w1).get("plan_sha256") if _mapping(w1) else None):
            errors.append("w1.invalid_approval")
        elif _mapping(w1)["plan_sha256"] != session.get("plan_sha256"):
            errors.append("w1.plan_sha256_mismatch")

    candidate = None
    if session.get("candidate") is not None:
        candidate = _validate_identity(
            errors,
            session["candidate"],
            "candidate",
            require_path=True,
            extra_keys={"plan_sha256"},
        )
        if not w1_approved:
            errors.append("candidate.requires_approved_w1")
        if candidate is not None and candidate.get("plan_sha256") != session.get("plan_sha256"):
            errors.append("candidate.plan_sha256_mismatch")

    verification = None
    if session.get("verification") is not None:
        if candidate is None:
            errors.append("verification.requires_candidate")
        verification = _validate_verification(
            errors, session["verification"], candidate, requirements
        )

    w2 = session.get("w2")
    w2_approved = _approval(w2, {"approved", "candidate_sha256", "verification_sha256"})
    if w2 is not None:
        item = _mapping(w2)
        if (
            not w2_approved
            or not _sha256(item.get("candidate_sha256") if item else None)
            or not _sha256(item.get("verification_sha256") if item else None)
        ):
            errors.append("w2.invalid_approval")
        else:
            if candidate is None:
                errors.append("w2.requires_candidate")
            elif item["candidate_sha256"] != candidate.get("sha256"):
                errors.append("w2.candidate_sha256_mismatch")
            if verification is None:
                errors.append("w2.requires_verification")
            elif item["verification_sha256"] != verification.get("sha256"):
                errors.append("w2.verification_sha256_mismatch")

    package = None
    if session.get("package") is not None:
        package = _validate_identity(
            errors,
            session["package"],
            "package",
            require_path=True,
            extra_keys={"candidate_sha256", "verification_sha256"},
        )
        if not isinstance(stage, str) or stage not in {"S5", "E1"}:
            errors.append("package.invalid_stage")
        if not w1_approved:
            errors.append("package.requires_approved_w1")
        if not w2_approved:
            errors.append("package.requires_approved_w2")
        if candidate is None:
            errors.append("package.requires_candidate")
        if verification is None:
            errors.append("package.requires_verification")
        if _has_required_failure(verification):
            errors.append("package.blocked_by_required_failure")
        if package is not None and candidate is not None and package.get("candidate_sha256") != candidate.get("sha256"):
            errors.append("package.candidate_sha256_mismatch")
        if package is not None and verification is not None and package.get("verification_sha256") != verification.get("sha256"):
            errors.append("package.verification_sha256_mismatch")

    w1_bound = (
        w1_approved
        and _mapping(w1) is not None
        and _mapping(w1).get("plan_sha256") == session.get("plan_sha256")
    )
    stage_requirements = {
        "approved_w1": {"S3", "S4", "W2", "S5", "E1"},
        "candidate": {"S4", "W2", "S5", "E1"},
        "verification": {"W2", "S5", "E1"},
        "approved_w2": {"S5", "E1"},
        "package": {"E1"},
    }
    prerequisites = {
        "approved_w1": w1_bound,
        "candidate": candidate is not None,
        "verification": verification is not None,
        "approved_w2": w2_approved,
        "package": package is not None,
    }
    if isinstance(stage, str) and stage in STAGES:
        for prerequisite, stages in stage_requirements.items():
            if stage in stages and not prerequisites[prerequisite]:
                errors.append(f"stage.{stage}.requires_{prerequisite}")

    return sorted(set(errors))


def session_gate_state(payload: object) -> str:
    """Return the workflow gate implied by a valid session document."""

    if validate_session(payload):
        return "INVALID"
    session = _mapping(payload)
    assert session is not None
    verification = _mapping(session.get("verification"))
    if _has_required_failure(verification):
        return "BLOCKED_REQUIRED_FAILURE"
    stage = session["stage"]
    if stage == "H1":
        return "PAUSED"
    if stage == "E2":
        return "CANCELLED"
    if stage in {"F1", "F2", "F3", "E3"}:
        return "BLOCKED"
    if stage in {"S0", "S1", "S2"}:
        return "PLANNING"
    if stage == "W1" and session.get("w1") is None:
        return "WAITING_FOR_W1"
    if stage in {"W1", "S3"}:
        return "BUILD_ALLOWED"
    if stage == "S4":
        return "VERIFYING"
    if stage == "W2" and session.get("w2") is None:
        return "WAITING_FOR_W2"
    if stage == "W2":
        return "PACKAGE_ALLOWED"
    if stage == "S5":
        return "PACKAGE_ALLOWED"
    return "COMPLETE"
