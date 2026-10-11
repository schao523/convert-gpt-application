"""Strict, path-safe contracts for Plugin Builder ZIP onboarding."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Literal, Mapping, TypeAlias, cast


OnboardingStatus: TypeAlias = Literal["BLOCKED", "FAIL"]
PackageSchema: TypeAlias = Literal["plugin-builder-package-v2", "plugin-builder-package-v3"]
ThirdPartyContent: TypeAlias = Literal["NONE", "INCLUDED_WITH_PLUGIN_NOTICES"]

_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_PLUGIN_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)

_METADATA_COMMON_KEYS = {
    "schema",
    "plugin_id",
    "archive_sha256",
    "candidate_sha256",
    "verification_sha256",
    "member_manifest_sha256",
    "members",
    "candidate_members",
    "envelope_profile",
    "preflight_evidence",
    "manifest_profile",
    "command_evidence",
    "fallback_activations",
    "evidence_states",
    "tool_bindings",
    "tool_contracts_sha256",
    "extracted_validation",
    "safety_validation",
}
_METADATA_V3_KEYS = {
    "capabilities_sha256",
    "realizations_sha256",
    "adapter_registry_sha256",
    "generated_runtime_configuration_sha256",
    "runtime_realizations",
    "runtime_realization_state",
}
_DECISION_KEYS = {
    "schema",
    "plugin_id",
    "version",
    "author",
    "license",
    "copyright_year",
    "redistribution_approved",
    "third_party_content_reviewed",
    "third_party_content",
    "public_marketplace_approved",
    "target_runtime",
    "marketplace_id",
    "codex_destination",
    "confirmed_by",
    "decision_recorded_at",
}
_AUTHORITY_KEYS = (
    "redistribution_approved",
    "third_party_content_reviewed",
    "public_marketplace_approved",
)


class OnboardingError(ValueError):
    """Stable onboarding failure whose identity contains no machine path."""

    def __init__(
        self,
        code: str,
        status: OnboardingStatus = "FAIL",
        detail: str = "",
    ) -> None:
        self.code = code
        self.status = status
        self.detail = detail
        super().__init__(code if not detail else f"{code}: {detail}")


@dataclass(frozen=True)
class PackageMember:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class CandidateMember:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class PackageMetadata:
    schema: PackageSchema
    plugin_id: str
    archive_sha256: str
    candidate_sha256: str
    verification_sha256: str
    member_manifest_sha256: str
    members: tuple[PackageMember, ...]
    candidate_members: tuple[CandidateMember, ...]
    envelope_profile: Literal["PORTABLE_SINGLE_DIRECTORY"]
    preflight_evidence: Mapping[str, object]
    manifest_profile: str
    command_evidence: tuple[Mapping[str, object], ...]
    fallback_activations: tuple[Mapping[str, object], ...]
    evidence_states: Mapping[str, object]
    tool_bindings: tuple[Mapping[str, object], ...]
    tool_contracts_sha256: str
    extracted_validation: Mapping[str, object]
    safety_validation: Mapping[str, object]
    capabilities_sha256: str | None = None
    realizations_sha256: str | None = None
    adapter_registry_sha256: str | None = None
    generated_runtime_configuration_sha256: str | None = None
    runtime_realizations: tuple[Mapping[str, object], ...] = ()
    runtime_realization_state: str | None = None


@dataclass(frozen=True)
class WorkbenchRepairMetadata:
    schema: Literal["workbench-repaired-plugin-v1"]
    plugin_id: str
    version: str
    archive_sha256: str
    source_archive_sha256: str
    member_manifest_sha256: str
    content_tree_sha256: str
    members: tuple[PackageMember, ...]
    input_profile: Literal["PLUGIN_BUILDER_CANDIDATE_V1"]
    envelope_profile: Literal["LEGACY_FLAT"]
    manifest_profile: Literal["PORTABLE_WITH_OPENAI_COMPATIBILITY"]
    repair_manifest_sha256: str
    producer_claims: Mapping[str, object]
    evidence_states: Mapping[str, object]
    extracted_validation: Mapping[str, object]
    safety_validation: Mapping[str, object]


@dataclass(frozen=True)
class PublicationDecisions:
    schema: Literal["plugin-publication-decisions-v1"]
    plugin_id: str
    version: str
    author: str
    license: Literal["MIT"]
    copyright_year: int
    redistribution_approved: Literal[True]
    third_party_content_reviewed: Literal[True]
    third_party_content: ThirdPartyContent
    public_marketplace_approved: Literal[True]
    target_runtime: Literal["CODEX"]
    marketplace_id: Literal["obvious-one"]
    codex_destination: str
    confirmed_by: str
    decision_recorded_at: str

    def identity_payload(self) -> dict[str, object]:
        """Return the owner decision payload excluding observation time."""

        return {
            "schema": self.schema,
            "plugin_id": self.plugin_id,
            "version": self.version,
            "author": self.author,
            "license": self.license,
            "copyright_year": self.copyright_year,
            "redistribution_approved": self.redistribution_approved,
            "third_party_content_reviewed": self.third_party_content_reviewed,
            "third_party_content": self.third_party_content,
            "public_marketplace_approved": self.public_marketplace_approved,
            "target_runtime": self.target_runtime,
            "marketplace_id": self.marketplace_id,
            "codex_destination": self.codex_destination,
            "confirmed_by": self.confirmed_by,
        }


def _load_json(path: Path, prefix: str) -> Mapping[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise OnboardingError(f"{prefix}.invalid_json") from exc
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise OnboardingError(f"{prefix}.invalid_type", detail="root")
    return value


def _exact_keys(
    value: Mapping[str, object],
    allowed: set[str],
    prefix: str,
    *,
    authority_keys: tuple[str, ...] = (),
) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise OnboardingError(f"{prefix}.unknown_key", detail=unknown[0])
    for key in authority_keys:
        if key not in value:
            raise OnboardingError(f"{prefix}.{key}_required", "BLOCKED")
    missing = sorted(allowed - set(value))
    if missing:
        raise OnboardingError(f"{prefix}.missing_key", detail=missing[0])


def _text(value: object, prefix: str, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise OnboardingError(f"{prefix}.invalid_{field}")
    return value


def _digest(value: object, prefix: str, field: str) -> str:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise OnboardingError(f"{prefix}.invalid_digest", detail=field)
    return value


def _mapping(value: object, prefix: str, field: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise OnboardingError(f"{prefix}.invalid_type", detail=field)
    return cast(Mapping[str, object], _freeze(value))


def _mapping_sequence(
    value: object, prefix: str, field: str
) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        raise OnboardingError(f"{prefix}.invalid_type", detail=field)
    return tuple(_mapping(item, prefix, f"{field}[]") for item in value)


def _freeze(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _members(
    value: object,
    prefix: str,
    field: str,
    member_type: type[PackageMember] | type[CandidateMember],
) -> tuple[PackageMember, ...] | tuple[CandidateMember, ...]:
    if not isinstance(value, list):
        raise OnboardingError(f"{prefix}.invalid_type", detail=field)
    members: list[PackageMember | CandidateMember] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "size", "sha256"}:
            raise OnboardingError(f"{prefix}.invalid_member", detail=field)
        path = _text(item.get("path"), prefix, "member_path")
        size = item.get("size")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise OnboardingError(f"{prefix}.invalid_member_size", detail=field)
        digest = _digest(item.get("sha256"), prefix, "member_sha256")
        members.append(member_type(path, size, digest))
    return tuple(members)  # type: ignore[return-value]


def load_package_metadata(path: Path) -> PackageMetadata:
    """Load one exact Plugin Builder v2 or v3 package sidecar."""

    prefix = "onboarding.metadata"
    payload = _load_json(path, prefix)
    schema = payload.get("schema")
    if schema not in {"plugin-builder-package-v2", "plugin-builder-package-v3"}:
        raise OnboardingError(f"{prefix}.unsupported_schema")
    allowed = _METADATA_COMMON_KEYS | (_METADATA_V3_KEYS if schema.endswith("v3") else set())
    _exact_keys(payload, allowed, prefix)
    plugin_id = _text(payload["plugin_id"], prefix, "plugin_id")
    if not _PLUGIN_ID.fullmatch(plugin_id):
        raise OnboardingError(f"{prefix}.invalid_plugin_id")
    envelope = payload["envelope_profile"]
    if envelope != "PORTABLE_SINGLE_DIRECTORY":
        raise OnboardingError(f"{prefix}.invalid_envelope_profile")

    v3 = schema.endswith("v3")
    runtime_state = payload.get("runtime_realization_state")
    if v3 and runtime_state != "NOT VERIFIED":
        raise OnboardingError(f"{prefix}.invalid_runtime_realization_state")
    return PackageMetadata(
        schema=cast(PackageSchema, schema),
        plugin_id=plugin_id,
        archive_sha256=_digest(payload["archive_sha256"], prefix, "archive_sha256"),
        candidate_sha256=_digest(payload["candidate_sha256"], prefix, "candidate_sha256"),
        verification_sha256=_digest(payload["verification_sha256"], prefix, "verification_sha256"),
        member_manifest_sha256=_digest(payload["member_manifest_sha256"], prefix, "member_manifest_sha256"),
        members=cast(tuple[PackageMember, ...], _members(payload["members"], prefix, "members", PackageMember)),
        candidate_members=cast(tuple[CandidateMember, ...], _members(payload["candidate_members"], prefix, "candidate_members", CandidateMember)),
        envelope_profile="PORTABLE_SINGLE_DIRECTORY",
        preflight_evidence=_mapping(payload["preflight_evidence"], prefix, "preflight_evidence"),
        manifest_profile=_text(payload["manifest_profile"], prefix, "manifest_profile"),
        command_evidence=_mapping_sequence(payload["command_evidence"], prefix, "command_evidence"),
        fallback_activations=_mapping_sequence(payload["fallback_activations"], prefix, "fallback_activations"),
        evidence_states=_mapping(payload["evidence_states"], prefix, "evidence_states"),
        tool_bindings=_mapping_sequence(payload["tool_bindings"], prefix, "tool_bindings"),
        tool_contracts_sha256=_digest(payload["tool_contracts_sha256"], prefix, "tool_contracts_sha256"),
        extracted_validation=_mapping(payload["extracted_validation"], prefix, "extracted_validation"),
        safety_validation=_mapping(payload["safety_validation"], prefix, "safety_validation"),
        capabilities_sha256=_digest(payload["capabilities_sha256"], prefix, "capabilities_sha256") if v3 else None,
        realizations_sha256=_digest(payload["realizations_sha256"], prefix, "realizations_sha256") if v3 else None,
        adapter_registry_sha256=_digest(payload["adapter_registry_sha256"], prefix, "adapter_registry_sha256") if v3 else None,
        generated_runtime_configuration_sha256=_digest(payload["generated_runtime_configuration_sha256"], prefix, "generated_runtime_configuration_sha256") if v3 else None,
        runtime_realizations=_mapping_sequence(payload["runtime_realizations"], prefix, "runtime_realizations") if v3 else (),
        runtime_realization_state=cast(str, runtime_state) if v3 else None,
    )


def load_onboarding_metadata(path: Path) -> PackageMetadata | WorkbenchRepairMetadata:
    """Load Plugin Builder metadata or Workbench-owned repair metadata."""

    payload = _load_json(path, "onboarding.metadata")
    if payload.get("schema") in {"plugin-builder-package-v2", "plugin-builder-package-v3"}:
        return load_package_metadata(path)
    prefix = "onboarding.metadata"
    keys = {
        "schema", "plugin_id", "version", "archive_sha256",
        "source_archive_sha256", "member_manifest_sha256", "content_tree_sha256",
        "members", "input_profile", "envelope_profile", "manifest_profile",
        "repair_manifest_sha256", "producer_claims", "evidence_states",
        "extracted_validation", "safety_validation",
    }
    _exact_keys(payload, keys, prefix)
    if payload.get("schema") != "workbench-repaired-plugin-v1":
        raise OnboardingError(f"{prefix}.unsupported_schema")
    plugin_id = _text(payload["plugin_id"], prefix, "plugin_id")
    if _PLUGIN_ID.fullmatch(plugin_id) is None:
        raise OnboardingError(f"{prefix}.invalid_plugin_id")
    version = _text(payload["version"], prefix, "version")
    if _SEMVER.fullmatch(version) is None:
        raise OnboardingError(f"{prefix}.invalid_version")
    if payload["input_profile"] != "PLUGIN_BUILDER_CANDIDATE_V1":
        raise OnboardingError(f"{prefix}.invalid_input_profile")
    if payload["envelope_profile"] != "LEGACY_FLAT":
        raise OnboardingError(f"{prefix}.invalid_envelope_profile")
    if payload["manifest_profile"] != "PORTABLE_WITH_OPENAI_COMPATIBILITY":
        raise OnboardingError(f"{prefix}.invalid_manifest_profile")
    states = _mapping(payload["evidence_states"], prefix, "evidence_states")
    if not states or set(states.values()) != {"NOT VERIFIED"}:
        raise OnboardingError(f"{prefix}.invalid_evidence_states")
    return WorkbenchRepairMetadata(
        schema="workbench-repaired-plugin-v1",
        plugin_id=plugin_id,
        version=version,
        archive_sha256=_digest(payload["archive_sha256"], prefix, "archive_sha256"),
        source_archive_sha256=_digest(payload["source_archive_sha256"], prefix, "source_archive_sha256"),
        member_manifest_sha256=_digest(payload["member_manifest_sha256"], prefix, "member_manifest_sha256"),
        content_tree_sha256=_digest(payload["content_tree_sha256"], prefix, "content_tree_sha256"),
        members=cast(tuple[PackageMember, ...], _members(payload["members"], prefix, "members", PackageMember)),
        input_profile="PLUGIN_BUILDER_CANDIDATE_V1",
        envelope_profile="LEGACY_FLAT",
        manifest_profile="PORTABLE_WITH_OPENAI_COMPATIBILITY",
        repair_manifest_sha256=_digest(payload["repair_manifest_sha256"], prefix, "repair_manifest_sha256"),
        producer_claims=_mapping(payload["producer_claims"], prefix, "producer_claims"),
        evidence_states=states,
        extracted_validation=_mapping(payload["extracted_validation"], prefix, "extracted_validation"),
        safety_validation=_mapping(payload["safety_validation"], prefix, "safety_validation"),
    )


def load_publication_decisions(path: Path) -> PublicationDecisions:
    """Load the exact owner authority record for Codex/Obvious One v1."""

    prefix = "onboarding.decisions"
    payload = _load_json(path, prefix)
    _exact_keys(payload, _DECISION_KEYS, prefix, authority_keys=_AUTHORITY_KEYS)
    if payload["schema"] != "plugin-publication-decisions-v1":
        raise OnboardingError(f"{prefix}.unsupported_schema")
    plugin_id = _text(payload["plugin_id"], prefix, "plugin_id")
    if not _PLUGIN_ID.fullmatch(plugin_id):
        raise OnboardingError(f"{prefix}.invalid_plugin_id")
    version = _text(payload["version"], prefix, "version")
    if not _SEMVER.fullmatch(version):
        raise OnboardingError(f"{prefix}.invalid_version")
    for key in _AUTHORITY_KEYS:
        if payload[key] is not True:
            raise OnboardingError(f"{prefix}.{key}_required", "BLOCKED")
    if payload["license"] != "MIT":
        raise OnboardingError(f"{prefix}.unsupported_license")
    author = _text(payload["author"], prefix, "author")
    year = payload["copyright_year"]
    if not isinstance(year, int) or isinstance(year, bool) or not 1900 <= year <= 9999:
        raise OnboardingError(f"{prefix}.invalid_copyright_year")
    third_party = payload["third_party_content"]
    if third_party not in {"NONE", "INCLUDED_WITH_PLUGIN_NOTICES"}:
        raise OnboardingError(f"{prefix}.invalid_third_party_content")
    if payload["target_runtime"] != "CODEX":
        raise OnboardingError(f"{prefix}.invalid_target_runtime")
    if payload["marketplace_id"] != "obvious-one":
        raise OnboardingError(f"{prefix}.invalid_marketplace_id")
    destination = payload["codex_destination"]
    if destination != f"plugins/{plugin_id}":
        raise OnboardingError(f"{prefix}.invalid_codex_destination")
    confirmed_by = _text(payload["confirmed_by"], prefix, "confirmed_by")
    recorded_at = _text(payload["decision_recorded_at"], prefix, "decision_recorded_at")
    try:
        parsed_time = datetime.fromisoformat(recorded_at)
    except ValueError as exc:
        raise OnboardingError(f"{prefix}.invalid_decision_recorded_at") from exc
    if parsed_time.tzinfo is None:
        raise OnboardingError(f"{prefix}.invalid_decision_recorded_at")
    return PublicationDecisions(
        schema="plugin-publication-decisions-v1",
        plugin_id=plugin_id,
        version=version,
        author=author,
        license="MIT",
        copyright_year=year,
        redistribution_approved=True,
        third_party_content_reviewed=True,
        third_party_content=cast(ThirdPartyContent, third_party),
        public_marketplace_approved=True,
        target_runtime="CODEX",
        marketplace_id="obvious-one",
        codex_destination=cast(str, destination),
        confirmed_by=confirmed_by,
        decision_recorded_at=recorded_at,
    )
