"""Strict owner-approved contract for delegated-reference ZIP repair."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re
from types import MappingProxyType
from typing import Mapping

from .contract import OnboardingError


_KEYS_V1 = {
    "schema",
    "plugin_id",
    "source_version",
    "target_version",
    "source_archive_sha256",
    "owner_skill",
    "non_owner_skills",
    "references",
    "source_manifest_path",
    "approval_record",
}
_KEYS_V2 = _KEYS_V1 | {"third_party_notice"}
_REFERENCE_KEYS = {"reference_id", "owner_relative_path", "sha256"}
_APPROVAL_KEYS = {"decision", "confirmed_by", "recorded_at"}
_NOTICE_KEYS = {
    "classification",
    "redistribution_approved",
    "confirmed_by",
    "recorded_at",
}
_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_REFERENCE_ID = re.compile(r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")
_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class RepairReference:
    reference_id: str
    owner_relative_path: str
    sha256: str


@dataclass(frozen=True)
class ThirdPartyNotice:
    classification: str
    redistribution_approved: bool
    confirmed_by: str
    recorded_at: str


@dataclass(frozen=True)
class DelegatedReferenceRepair:
    schema: str
    plugin_id: str
    source_version: str
    target_version: str
    source_archive_sha256: str
    owner_skill: str
    non_owner_skills: tuple[str, ...]
    references: tuple[RepairReference, ...]
    source_manifest_path: str
    approval_record: Mapping[str, str]
    third_party_notice: ThirdPartyNotice | None


def _fail(code: str, detail: str = "") -> OnboardingError:
    return OnboardingError(f"onboarding.repair_contract.{code}", "FAIL", detail)


def _text(value: object, code: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise _fail(code)
    return value


def _path(value: object) -> str:
    text = _text(value, "invalid_path")
    if "\\" in text:
        raise _fail("invalid_path")
    path = PurePosixPath(text)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise _fail("invalid_path")
    return path.as_posix()


def load_repair_contract(path: Path) -> DelegatedReferenceRepair:
    """Load an exact, owner-approved delegated-reference repair contract."""

    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _fail("invalid_json") from exc
    if not isinstance(payload, dict):
        raise _fail("invalid_type")
    schema = payload.get("schema")
    if schema not in {
        "plugin-delegated-reference-repair-v1",
        "plugin-delegated-reference-repair-v2",
    }:
        if "schema" not in payload:
            raise _fail("missing_key", "schema")
        raise _fail("unsupported_schema")
    keys = _KEYS_V2 if schema == "plugin-delegated-reference-repair-v2" else _KEYS_V1
    unknown = sorted(set(payload) - keys)
    if unknown:
        raise _fail("unknown_key", unknown[0])
    missing = sorted(keys - set(payload))
    if missing:
        raise _fail("missing_key", missing[0])
    plugin_id = _text(payload["plugin_id"], "invalid_plugin_id")
    owner = _text(payload["owner_skill"], "invalid_owner_skill")
    if _NAME.fullmatch(plugin_id) is None:
        raise _fail("invalid_plugin_id")
    if _NAME.fullmatch(owner) is None:
        raise _fail("invalid_owner_skill")
    source_version = _text(payload["source_version"], "invalid_source_version")
    target_version = _text(payload["target_version"], "invalid_target_version")
    if _SEMVER.fullmatch(source_version) is None:
        raise _fail("invalid_source_version")
    if _SEMVER.fullmatch(target_version) is None or target_version == source_version:
        raise _fail("invalid_target_version")
    digest = _text(payload["source_archive_sha256"], "invalid_digest")
    if _DIGEST.fullmatch(digest) is None:
        raise _fail("invalid_digest")
    raw_non_owners = payload["non_owner_skills"]
    if not isinstance(raw_non_owners, list) or not raw_non_owners:
        raise _fail("invalid_non_owner_skills")
    non_owners: list[str] = []
    for item in raw_non_owners:
        value = _text(item, "invalid_non_owner_skill")
        if _NAME.fullmatch(value) is None:
            raise _fail("invalid_non_owner_skill")
        if value in non_owners:
            raise _fail("duplicate_non_owner_skill", value)
        non_owners.append(value)
    if owner in non_owners:
        raise _fail("owner_is_non_owner")
    raw_references = payload["references"]
    if not isinstance(raw_references, list) or not raw_references:
        raise _fail("invalid_references")
    references: list[RepairReference] = []
    seen: set[str] = set()
    for item in raw_references:
        if not isinstance(item, dict) or set(item) != _REFERENCE_KEYS:
            raise _fail("invalid_reference")
        reference_id = _text(item["reference_id"], "invalid_reference_id")
        if _REFERENCE_ID.fullmatch(reference_id) is None:
            raise _fail("invalid_reference_id")
        if reference_id in seen:
            raise _fail("duplicate_reference", reference_id)
        seen.add(reference_id)
        reference_digest = _text(item["sha256"], "invalid_digest")
        if _DIGEST.fullmatch(reference_digest) is None:
            raise _fail("invalid_digest", reference_id)
        references.append(
            RepairReference(reference_id, _path(item["owner_relative_path"]), reference_digest)
        )
    approval = payload["approval_record"]
    if (
        not isinstance(approval, dict)
        or set(approval) != _APPROVAL_KEYS
        or approval.get("decision") != "APPROVED"
        or not isinstance(approval.get("confirmed_by"), str)
        or not approval["confirmed_by"].strip()
        or not isinstance(approval.get("recorded_at"), str)
        or not approval["recorded_at"].strip()
    ):
        raise _fail("approval_required")
    third_party_notice: ThirdPartyNotice | None = None
    if schema == "plugin-delegated-reference-repair-v2":
        notice = payload["third_party_notice"]
        if (
            not isinstance(notice, dict)
            or set(notice) != _NOTICE_KEYS
            or notice.get("classification") != "PUBLIC_DOMAIN"
            or not isinstance(notice.get("confirmed_by"), str)
            or not notice["confirmed_by"].strip()
            or not isinstance(notice.get("recorded_at"), str)
            or re.fullmatch(r"\d{4}-\d{2}-\d{2}", notice["recorded_at"]) is None
        ):
            raise _fail("invalid_third_party_notice")
        if notice.get("redistribution_approved") is not True:
            raise _fail("redistribution_approval_required")
        third_party_notice = ThirdPartyNotice(
            classification="PUBLIC_DOMAIN",
            redistribution_approved=True,
            confirmed_by=notice["confirmed_by"],
            recorded_at=notice["recorded_at"],
        )
    return DelegatedReferenceRepair(
        schema=schema,
        plugin_id=plugin_id,
        source_version=source_version,
        target_version=target_version,
        source_archive_sha256=digest,
        owner_skill=owner,
        non_owner_skills=tuple(non_owners),
        references=tuple(references),
        source_manifest_path=_path(payload["source_manifest_path"]),
        approval_record=MappingProxyType(
            {key: str(approval[key]) for key in sorted(_APPROVAL_KEYS)}
        ),
        third_party_notice=third_party_notice,
    )
