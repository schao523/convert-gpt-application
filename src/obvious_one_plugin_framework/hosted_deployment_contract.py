"""Strict contracts for complete OpenAI-hosted plugin deployment archives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Literal, Mapping

from .contract import ContractError, DistributionContract, load_contract
from .verification import (
    ApplicationConfig,
    VerificationConfigError,
    load_application_config_path,
)


DeploymentOperation = Literal["OPENAI_HOSTED_CREATE", "OPENAI_HOSTED_UPDATE"]
ChannelStatus = Literal[
    "UNPUBLISHED", "PENDING_ACTION", "CURRENT_BY_DECLARATION", "STALE", "UNKNOWN"
]

_OPERATIONS = frozenset({"OPENAI_HOSTED_CREATE", "OPENAI_HOSTED_UPDATE"})
_CHANNEL_STATUSES = frozenset(
    {"UNPUBLISHED", "PENDING_ACTION", "CURRENT_BY_DECLARATION", "STALE", "UNKNOWN"}
)
_PROVIDERS = frozenset({"packaged_executable", "hosted_native", "external_adapter"})
_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")
_SENSITIVE_KEY = re.compile(r"(?:credential|password|secret|token|workspace)", re.I)

_ROOT_KEYS = {"schema_version", "application_id", "operation", "lineage", "identity", "target", "content", "validation", "channels"}
_LINEAGE_KEYS = {"source_inventory", "canonical_distribution_contract", "hosted_lineage_decision"}
_IDENTITY_KEYS = {"package_name", "record"}
_TARGET_KEYS = {"version", "archive_name", "portable_manifest", "legacy_manifest", "max_archive_bytes"}
_CONTENT_KEYS = {"canonical_mappings", "adapter_mappings"}
_VALIDATION_KEYS = {"expected_skills", "explicit_only_skills", "required_application_tests", "capabilities"}
_MAPPING_KEYS = {"id", "source_kind", "source", "target", "copy_mode", "classification", "redistribution_reference"}
_CAPABILITY_KEYS = {"id", "requirement", "provider_kind", "artifact_paths", "local_verification_test", "hosted_verification", "on_unavailable", "fallback"}
_FALLBACK_KEYS = {"description", "artifact_paths", "approval_reference"}
_CHANNEL_KEYS = {"status", "evidence"}
_IDENTITY_RECORD_KEYS = {"schema_version", "application_id", "package_name", "last_confirmed_version", "last_confirmed_archive_sha256", "origin", "deployment_confirmation"}
_CONFIRMATION_KEYS = {"status", "recorded_at", "evidence_reference"}
_LINEAGE_DECISION_KEYS = {"schema_version", "application_id", "status", "canonical_source", "evidence_reference"}


class HostedDeploymentError(ValueError):
    """Raised when hosted deployment input violates a stable rule."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code if not detail else f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class HostedIdentityRecord:
    application_id: str
    package_name: str
    last_confirmed_version: str
    last_confirmed_archive_sha256: str
    origin: Literal["imported_hosted_archive", "prior_verified_deployment"]
    recorded_at: str
    evidence_reference: str


@dataclass(frozen=True)
class DeploymentMapping:
    mapping_id: str
    source_kind: Literal["canonical_application", "hosted_adapter"]
    source: str
    target: str
    copy_mode: Literal["copy_file", "copy_tree"]
    classification: Literal["text", "binary"]
    redistribution_reference: str


@dataclass(frozen=True)
class CapabilityFallback:
    description: str
    artifact_paths: tuple[str, ...]
    approval_reference: str


@dataclass(frozen=True)
class CapabilityContract:
    capability_id: str
    requirement: Literal["required", "optional"]
    provider_kind: Literal["packaged_executable", "hosted_native", "external_adapter"]
    artifact_paths: tuple[str, ...]
    local_verification_test: str | None
    hosted_verification: Literal["required_after_install"]
    on_unavailable: Literal["block", "use_declared_fallback"]
    fallback: CapabilityFallback | None


@dataclass(frozen=True)
class ChannelRecord:
    status: ChannelStatus
    evidence: str


@dataclass(frozen=True)
class HostedDeploymentContract:
    schema_version: int
    application_id: str
    operation: DeploymentOperation
    contract_path: Path
    application_root: Path
    application: ApplicationConfig
    source_inventory: Path
    distribution_contract: Path
    distribution: DistributionContract
    lineage_decision: Path
    package_name: str
    identity_record: HostedIdentityRecord | None
    target_version: str
    archive_name: str
    portable_manifest: str
    legacy_manifest: str
    max_archive_bytes: int
    canonical_mappings: tuple[DeploymentMapping, ...]
    adapter_mappings: tuple[DeploymentMapping, ...]
    expected_skills: tuple[str, ...]
    explicit_only_skills: tuple[str, ...]
    required_application_tests: tuple[str, ...]
    capabilities: tuple[CapabilityContract, ...]
    channels: Mapping[str, ChannelRecord]


def _load_json(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HostedDeploymentError("invalid_json", label) from exc
    if not isinstance(value, dict):
        raise HostedDeploymentError("invalid_type", f"{label} must be an object")
    return value


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise HostedDeploymentError("invalid_type", f"{label} must be an object")
    return value


def _only_keys(value: Mapping[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise HostedDeploymentError("unknown_key", f"{label}.{unknown[0]}")
    missing = sorted(allowed - set(value))
    if missing:
        raise HostedDeploymentError("missing_key", f"{label}.{missing[0]}")


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise HostedDeploymentError("invalid_text", label)
    return value


def _relative(value: Any, label: str) -> str:
    text = _text(value, label)
    if "\\" in text or _WINDOWS_DRIVE.match(text) or text.startswith(("/", "//")):
        raise HostedDeploymentError("invalid_relative_path", label)
    path = PurePosixPath(text)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise HostedDeploymentError("invalid_relative_path", label)
    return path.as_posix()


def _reference(value: Any, label: str, *, base: Path, boundary: Path, must_exist: bool = True) -> tuple[str, Path]:
    text = _text(value, label)
    if "\\" in text or _WINDOWS_DRIVE.match(text) or text.startswith(("/", "//")):
        raise HostedDeploymentError("invalid_relative_path", label)
    parts = PurePosixPath(text).parts
    if any(part in {"", "."} for part in parts):
        raise HostedDeploymentError("invalid_relative_path", label)
    resolved = (base / Path(*parts)).resolve()
    if not resolved.is_relative_to(boundary.resolve()):
        raise HostedDeploymentError("invalid_relative_path", label)
    if must_exist and not resolved.is_file():
        raise HostedDeploymentError("referenced_file_missing", label)
    return text, resolved


def _string_list(value: Any, label: str, *, paths: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise HostedDeploymentError("invalid_type", f"{label} must be a list")
    items = tuple(_relative(item, label) if paths else _text(item, label) for item in value)
    if len(items) != len(set(items)):
        raise HostedDeploymentError("duplicate_value", label)
    return items


def _semver(value: Any, label: str) -> str:
    text = _text(value, label)
    match = _SEMVER.fullmatch(text)
    if match is None:
        raise HostedDeploymentError("invalid_semver", label)
    prerelease = match.group(4)
    if prerelease is not None and any(
        item.isdigit() and len(item) > 1 and item.startswith("0")
        for item in prerelease.split(".")
    ):
        raise HostedDeploymentError("invalid_semver", label)
    return text


def _semver_key(value: str) -> tuple[int, int, int, tuple[tuple[int, int | str], ...]]:
    match = _SEMVER.fullmatch(value)
    if match is None:
        raise HostedDeploymentError("invalid_semver", value)
    prerelease = match.group(4)
    if prerelease is None:
        pre_key: tuple[tuple[int, int | str], ...] = ((2, ""),)
    else:
        parts: list[tuple[int, int | str]] = []
        for item in prerelease.split("."):
            parts.append((0, int(item)) if item.isdigit() else (1, item))
        pre_key = tuple(parts)
    return int(match.group(1)), int(match.group(2)), int(match.group(3)), pre_key


def _is_newer(candidate: str, current: str) -> bool:
    return _semver_key(candidate) > _semver_key(current)


def _timestamp(value: Any, label: str) -> str:
    text = _text(value, label)
    if not text.endswith("Z"):
        raise HostedDeploymentError("invalid_timestamp", label)
    try:
        datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise HostedDeploymentError("invalid_timestamp", label) from exc
    return text


def _reject_sensitive_identity(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _SENSITIVE_KEY.search(str(key)):
                raise HostedDeploymentError("sensitive_identity_field", str(key))
            _reject_sensitive_identity(item)
    elif isinstance(value, list):
        for item in value:
            _reject_sensitive_identity(item)
    elif isinstance(value, str):
        if _WINDOWS_DRIVE.match(value) or value.startswith(("/", "\\\\")):
            raise HostedDeploymentError("sensitive_identity_field", "absolute_path")


def _application_root_for(path: Path) -> Path:
    return next(
        (candidate for candidate in path.parents if (candidate / "conversion.json").is_file()),
        path.parent.parent,
    )


def load_hosted_identity(path: Path) -> HostedIdentityRecord:
    identity_path = Path(path).resolve()
    raw = _load_json(identity_path, "hosted_identity")
    if raw.get("proposal_schema") == "hosted-identity-proposal-v1":
        raise HostedDeploymentError("hosted_identity_unapproved")
    _reject_sensitive_identity(raw)
    _only_keys(raw, _IDENTITY_RECORD_KEYS, "hosted_identity")
    if raw["schema_version"] != 1:
        raise HostedDeploymentError("unsupported_hosted_identity_schema", str(raw["schema_version"]))
    confirmation = _mapping(raw["deployment_confirmation"], "deployment_confirmation")
    _only_keys(confirmation, _CONFIRMATION_KEYS, "deployment_confirmation")
    if confirmation["status"] != "owner_confirmed":
        raise HostedDeploymentError("hosted_identity_unapproved")
    origin = _text(raw["origin"], "origin")
    if origin not in {"imported_hosted_archive", "prior_verified_deployment"}:
        raise HostedDeploymentError("invalid_identity_origin", origin)
    digest = _text(raw["last_confirmed_archive_sha256"], "last_confirmed_archive_sha256").lower()
    if not _DIGEST.fullmatch(digest):
        raise HostedDeploymentError("invalid_digest", "last_confirmed_archive_sha256")
    application_root = _application_root_for(identity_path)
    evidence, _ = _reference(
        confirmation["evidence_reference"],
        "deployment_confirmation.evidence_reference",
        base=identity_path.parent,
        boundary=application_root,
    )
    return HostedIdentityRecord(
        application_id=_text(raw["application_id"], "application_id"),
        package_name=_text(raw["package_name"], "package_name"),
        last_confirmed_version=_semver(raw["last_confirmed_version"], "last_confirmed_version"),
        last_confirmed_archive_sha256=digest,
        origin=origin,
        recorded_at=_timestamp(confirmation["recorded_at"], "deployment_confirmation.recorded_at"),
        evidence_reference=evidence,
    )


def _parse_mapping(value: Any, label: str, expected_kind: str) -> DeploymentMapping:
    raw = _mapping(value, label)
    _only_keys(raw, _MAPPING_KEYS, label)
    source_kind = _text(raw["source_kind"], f"{label}.source_kind")
    if source_kind != expected_kind:
        raise HostedDeploymentError("invalid_mapping_source_kind", label)
    copy_mode = _text(raw["copy_mode"], f"{label}.copy_mode")
    if copy_mode not in {"copy_file", "copy_tree"}:
        raise HostedDeploymentError("invalid_copy_mode", label)
    classification = _text(raw["classification"], f"{label}.classification")
    if classification not in {"text", "binary"}:
        raise HostedDeploymentError("invalid_content_classification", label)
    return DeploymentMapping(
        mapping_id=_text(raw["id"], f"{label}.id"),
        source_kind=source_kind,
        source=_relative(raw["source"], f"{label}.source"),
        target=_relative(raw["target"], f"{label}.target"),
        copy_mode=copy_mode,
        classification=classification,
        redistribution_reference=_text(raw["redistribution_reference"], f"{label}.redistribution_reference"),
    )


def _parse_capability(value: Any, label: str, command_ids: set[str]) -> CapabilityContract:
    raw = _mapping(value, label)
    _only_keys(raw, _CAPABILITY_KEYS, label)
    capability_id = _text(raw["id"], f"{label}.id")
    requirement = _text(raw["requirement"], f"{label}.requirement")
    if requirement not in {"required", "optional"}:
        raise HostedDeploymentError("invalid_capability_requirement", capability_id)
    provider = _text(raw["provider_kind"], f"{label}.provider_kind")
    if provider not in _PROVIDERS:
        raise HostedDeploymentError("invalid_capability_provider", capability_id)
    artifacts = _string_list(raw["artifact_paths"], f"{label}.artifact_paths", paths=True)
    if provider == "packaged_executable" and not artifacts:
        raise HostedDeploymentError("required_capability_artifact_missing", capability_id)
    if provider != "packaged_executable" and artifacts:
        raise HostedDeploymentError("invalid_capability_artifacts", capability_id)
    local_test = raw["local_verification_test"]
    if local_test is not None:
        local_test = _text(local_test, f"{label}.local_verification_test")
        if local_test not in command_ids:
            raise HostedDeploymentError("unknown_application_test", local_test)
    if raw["hosted_verification"] != "required_after_install":
        raise HostedDeploymentError("invalid_hosted_verification", capability_id)
    policy = _text(raw["on_unavailable"], f"{label}.on_unavailable")
    if policy not in {"block", "use_declared_fallback"}:
        raise HostedDeploymentError("invalid_capability_policy", capability_id)
    fallback_raw = raw["fallback"]
    fallback = None
    if fallback_raw is not None:
        item = _mapping(fallback_raw, f"{label}.fallback")
        _only_keys(item, _FALLBACK_KEYS, f"{label}.fallback")
        fallback = CapabilityFallback(
            description=_text(item["description"], f"{label}.fallback.description"),
            artifact_paths=_string_list(item["artifact_paths"], f"{label}.fallback.artifact_paths", paths=True),
            approval_reference=_text(item["approval_reference"], f"{label}.fallback.approval_reference"),
        )
    if requirement == "required" and (policy != "block" or fallback is not None):
        raise HostedDeploymentError("invalid_required_capability_policy", capability_id)
    if requirement == "optional" and policy == "use_declared_fallback" and fallback is None:
        raise HostedDeploymentError("capability_decision_required", capability_id)
    if policy == "block" and fallback is not None:
        raise HostedDeploymentError("invalid_capability_policy", capability_id)
    return CapabilityContract(
        capability_id=capability_id,
        requirement=requirement,
        provider_kind=provider,
        artifact_paths=artifacts,
        local_verification_test=local_test,
        hosted_verification="required_after_install",
        on_unavailable=policy,
        fallback=fallback,
    )


def _parse_channel(value: Any, label: str) -> ChannelRecord:
    raw = _mapping(value, label)
    _only_keys(raw, _CHANNEL_KEYS, label)
    status = _text(raw["status"], f"{label}.status")
    if status not in _CHANNEL_STATUSES:
        raise HostedDeploymentError("invalid_channel_status", status)
    try:
        evidence = _text(raw["evidence"], f"{label}.evidence")
    except HostedDeploymentError as exc:
        raise HostedDeploymentError("channel_evidence_required", label) from exc
    return ChannelRecord(status=status, evidence=evidence)


def _validate_lineage(path: Path, application_id: str, application_root: Path) -> None:
    raw = _load_json(path, "lineage_decision")
    _only_keys(raw, _LINEAGE_DECISION_KEYS, "lineage_decision")
    if raw["schema_version"] != 1 or raw["application_id"] != application_id:
        raise HostedDeploymentError("hosted_lineage_unresolved")
    if raw["status"] != "approved" or raw["canonical_source"] != "canonical_converted_application":
        raise HostedDeploymentError("hosted_lineage_unresolved")
    _reference(raw["evidence_reference"], "lineage_decision.evidence_reference", base=path.parent, boundary=application_root)


def load_hosted_deployment_contract(path: Path) -> HostedDeploymentContract:
    contract_path = Path(path).resolve()
    application_root = _application_root_for(contract_path)
    raw = _load_json(contract_path, "hosted_deployment")
    _only_keys(raw, _ROOT_KEYS, "hosted_deployment")
    if raw["schema_version"] != 1:
        raise HostedDeploymentError("unsupported_hosted_deployment_schema", str(raw["schema_version"]))
    application_id = _text(raw["application_id"], "application_id")
    operation = _text(raw["operation"], "operation")
    if operation not in _OPERATIONS:
        raise HostedDeploymentError("invalid_operation", operation)

    try:
        application = load_application_config_path(application_root / "conversion.json", application_root)
    except VerificationConfigError as exc:
        raise HostedDeploymentError("invalid_application_config", str(exc)) from exc
    if application.application_id != application_id:
        raise HostedDeploymentError("application_identity_mismatch", application_id)

    lineage = _mapping(raw["lineage"], "lineage")
    _only_keys(lineage, _LINEAGE_KEYS, "lineage")
    _, source_inventory = _reference(lineage["source_inventory"], "lineage.source_inventory", base=contract_path.parent, boundary=application_root)
    _, distribution_path = _reference(lineage["canonical_distribution_contract"], "lineage.canonical_distribution_contract", base=contract_path.parent, boundary=application_root)
    _, lineage_path = _reference(lineage["hosted_lineage_decision"], "lineage.hosted_lineage_decision", base=contract_path.parent, boundary=application_root)
    try:
        distribution = load_contract(distribution_path)
    except ContractError as exc:
        raise HostedDeploymentError("invalid_distribution_contract", exc.code) from exc
    if distribution.schema_version != 3:
        raise HostedDeploymentError("legacy_contract_read_only", str(distribution.schema_version))
    if distribution_path != application.distribution_contract:
        raise HostedDeploymentError("distribution_contract_mismatch")
    _validate_lineage(lineage_path, application_id, application_root)

    identity = _mapping(raw["identity"], "identity")
    _only_keys(identity, _IDENTITY_KEYS, "identity")
    package_name = _text(identity["package_name"], "identity.package_name")
    identity_record = None
    if operation == "OPENAI_HOSTED_CREATE":
        if identity["record"] is not None:
            raise HostedDeploymentError("hosted_identity_forbidden")
    else:
        if identity["record"] is None:
            raise HostedDeploymentError("hosted_identity_required")
        identity_ref = _text(identity["record"], "identity.record")
        if "proposal" in PurePosixPath(identity_ref).name:
            raise HostedDeploymentError("hosted_identity_unapproved")
        _, identity_path = _reference(identity_ref, "identity.record", base=contract_path.parent, boundary=application_root)
        identity_record = load_hosted_identity(identity_path)
        if identity_record.application_id != application_id:
            raise HostedDeploymentError("application_identity_mismatch", identity_record.application_id)
        if identity_record.package_name != package_name:
            raise HostedDeploymentError("hosted_package_name_mismatch")

    target = _mapping(raw["target"], "target")
    _only_keys(target, _TARGET_KEYS, "target")
    target_version = _semver(target["version"], "target.version")
    if identity_record is not None and not _is_newer(target_version, identity_record.last_confirmed_version):
        raise HostedDeploymentError("hosted_version_not_advanced")
    archive_name = _relative(target["archive_name"], "target.archive_name")
    if "/" in archive_name or not archive_name.lower().endswith(".zip"):
        raise HostedDeploymentError("invalid_archive_name", archive_name)
    portable_manifest = _relative(target["portable_manifest"], "target.portable_manifest")
    legacy_manifest = _relative(target["legacy_manifest"], "target.legacy_manifest")
    max_archive_bytes = target["max_archive_bytes"]
    if not isinstance(max_archive_bytes, int) or isinstance(max_archive_bytes, bool) or max_archive_bytes <= 0:
        raise HostedDeploymentError("invalid_size_limit", "target.max_archive_bytes")

    content = _mapping(raw["content"], "content")
    _only_keys(content, _CONTENT_KEYS, "content")
    canonical_raw = content["canonical_mappings"]
    adapter_raw = content["adapter_mappings"]
    if not isinstance(canonical_raw, list) or not isinstance(adapter_raw, list):
        raise HostedDeploymentError("invalid_type", "content mappings must be lists")
    canonical = tuple(_parse_mapping(item, f"canonical_mappings[{index}]", "canonical_application") for index, item in enumerate(canonical_raw))
    adapters = tuple(_parse_mapping(item, f"adapter_mappings[{index}]", "hosted_adapter") for index, item in enumerate(adapter_raw))
    all_mappings = canonical + adapters
    ids = [item.mapping_id for item in all_mappings]
    if len(ids) != len(set(ids)):
        raise HostedDeploymentError("duplicate_mapping_id")
    targets = [item.target.casefold() for item in all_mappings]
    if len(targets) != len(set(targets)):
        raise HostedDeploymentError("target_path_collision")

    validation = _mapping(raw["validation"], "validation")
    _only_keys(validation, _VALIDATION_KEYS, "validation")
    expected_skills = _string_list(validation["expected_skills"], "validation.expected_skills")
    explicit_only = _string_list(validation["explicit_only_skills"], "validation.explicit_only_skills")
    if not set(explicit_only) <= set(expected_skills):
        raise HostedDeploymentError("explicit_skill_not_expected")
    required_tests = _string_list(validation["required_application_tests"], "validation.required_application_tests")
    command_ids = {item.command_id for item in application.verification.commands}
    unknown_tests = sorted(set(required_tests) - command_ids)
    if unknown_tests:
        raise HostedDeploymentError("unknown_application_test", unknown_tests[0])
    capabilities_raw = validation["capabilities"]
    if not isinstance(capabilities_raw, list):
        raise HostedDeploymentError("invalid_type", "validation.capabilities must be a list")
    capabilities = tuple(_parse_capability(item, f"capabilities[{index}]", command_ids) for index, item in enumerate(capabilities_raw))
    capability_ids = [item.capability_id for item in capabilities]
    if len(capability_ids) != len(set(capability_ids)):
        raise HostedDeploymentError("duplicate_capability_id")

    channels_raw = _mapping(raw["channels"], "channels")
    _only_keys(channels_raw, {"openai_hosted", "obvious_one", "openai_public"}, "channels")
    channels = {key: _parse_channel(channels_raw[key], f"channels.{key}") for key in sorted(channels_raw)}

    return HostedDeploymentContract(
        schema_version=1,
        application_id=application_id,
        operation=operation,
        contract_path=contract_path,
        application_root=application_root,
        application=application,
        source_inventory=source_inventory,
        distribution_contract=distribution_path,
        distribution=distribution,
        lineage_decision=lineage_path,
        package_name=package_name,
        identity_record=identity_record,
        target_version=target_version,
        archive_name=archive_name,
        portable_manifest=portable_manifest,
        legacy_manifest=legacy_manifest,
        max_archive_bytes=max_archive_bytes,
        canonical_mappings=canonical,
        adapter_mappings=adapters,
        expected_skills=expected_skills,
        explicit_only_skills=explicit_only,
        required_application_tests=required_tests,
        capabilities=capabilities,
        channels=channels,
    )
