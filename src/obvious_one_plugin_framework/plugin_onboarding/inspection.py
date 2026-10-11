"""Safe inspection of evidence-bound Plugin Builder archives."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
from types import MappingProxyType
from typing import Mapping
import zipfile

from .. import plugin_authoring
from ..package_builder import FORBIDDEN_NAMES, SECRET_FRAGMENTS
from .contract import (
    OnboardingError,
    PackageMember,
    PackageMetadata,
    WorkbenchRepairMetadata,
)


_CREDENTIAL = re.compile(
    r"(?i)(?:api[_-]?key|credential|password|secret|token)\s*[:=]"
)
_FORBIDDEN_CREDENTIAL_NAMES = frozenset(FORBIDDEN_NAMES) | frozenset(
    {"credentials.json", "id_rsa", "id_dsa"}
)
_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
)
_DEVELOPMENT_IMPORTS = ("obvious_one_plugin_framework", "plugin_builder_core")
_DEPENDENCY_FILES = frozenset(
    {
        "requirements.txt",
        "pyproject.toml",
        "poetry.lock",
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
    }
)
_EXECUTABLE_SUFFIXES = frozenset({".py", ".js", ".mjs", ".cjs", ".ps1", ".sh", ".exe"})
_EVIDENCE_LAYERS = (
    "installation",
    "skill_invocation",
    "capability_discovery",
    "operation_execution",
    "result_delivery",
    "conversation",
)
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(_json_value(value), ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("ascii")


def _json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


@dataclass(frozen=True)
class OnboardingInspection:
    schema: str
    plugin_id: str
    version: str
    package_state: str
    archive_sha256: str
    candidate_sha256: str | None
    verification_sha256: str | None
    content_tree_sha256: str
    member_manifest_sha256: str
    members: tuple[PackageMember, ...]
    candidate_members: tuple[object, ...]
    manifest_profile: str
    manifest_identity: Mapping[str, object]
    preflight_evidence: Mapping[str, object]
    preflight_evidence_sha256: str
    command_evidence: tuple[Mapping[str, object], ...]
    fallback_activations: tuple[Mapping[str, object], ...]
    producer_evidence_states: Mapping[str, object]
    tool_bindings: tuple[Mapping[str, object], ...]
    tool_contracts_sha256: str
    tool_contracts: tuple[Mapping[str, object], ...]
    offline_validator_files: tuple[str, ...]
    mcp_files: tuple[str, ...]
    dependency_files: tuple[str, ...]
    executable_files: tuple[str, ...]
    executed_files: tuple[str, ...]
    runtime_realization_state: str
    capabilities_sha256: str | None
    realizations_sha256: str | None
    adapter_registry_sha256: str | None
    generated_runtime_configuration_sha256: str | None
    runtime_realizations: tuple[Mapping[str, object], ...]
    evidence_states: Mapping[str, str]
    evidence_bundle_state: str
    input_profile: str
    producer_claims: Mapping[str, object]
    diagnostics: tuple[str, ...] = ()


def _fail(code: str, detail: str = "") -> OnboardingError:
    return OnboardingError(f"onboarding.inspection.{code}", "FAIL", detail)


def _load_json(path: Path, code: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _fail(code) from exc
    if not isinstance(value, dict):
        raise _fail(code)
    return value


def _member_tuple(member: object) -> tuple[object, ...]:
    return (getattr(member, "path"), getattr(member, "size"), getattr(member, "sha256"))


def _validate_metadata_closure(
    inventory: plugin_authoring.ArchiveInventory,
    metadata: PackageMetadata,
) -> None:
    if inventory.archive_sha256 != metadata.archive_sha256:
        raise _fail("archive_sha256_mismatch")
    expected_member_digest = sha256(
        _canonical_bytes([asdict(member) for member in metadata.members])
    ).hexdigest()
    if expected_member_digest != metadata.member_manifest_sha256:
        raise _fail("member_manifest_sha256_mismatch")
    if tuple(map(_member_tuple, inventory.members)) != tuple(
        map(_member_tuple, metadata.members)
    ):
        raise _fail("archive_members_mismatch")
    for field, validation in (
        ("extracted_validation", metadata.extracted_validation),
        ("safety_validation", metadata.safety_validation),
    ):
        if (
            set(validation) != {"state", "diagnostics"}
            or validation.get("state") != "PASS"
            or validation.get("diagnostics") not in ((), [])
        ):
            raise _fail(f"{field}_invalid")
    if metadata.preflight_evidence.get("manifest_profile") != metadata.manifest_profile:
        raise _fail("manifest_profile_mismatch")


def _manifest_identity(root: Path, metadata: PackageMetadata) -> tuple[dict[str, object], str, tuple[Mapping[str, object], ...]]:
    portable = _load_json(root / "plugin.json", "portable_manifest_invalid")
    compatibility = _load_json(
        root / ".codex-plugin" / "plugin.json", "compatibility_manifest_invalid"
    )
    issues = plugin_authoring.validate_plugin_tree(root)
    if issues:
        issue = issues[0]
        raise _fail("plugin_tree_invalid", f"{issue.code}:{issue.path}")
    if portable.get("name") != metadata.plugin_id:
        raise _fail("plugin_identity_mismatch")
    extensions = portable.get("extensions")
    if not isinstance(extensions, dict):
        raise _fail("portable_manifest_invalid")
    openai = extensions.get("com.openai")
    if not isinstance(openai, dict) or not isinstance(openai.get("interface"), dict):
        raise _fail("portable_manifest_invalid")
    interface = openai["interface"]
    author = portable.get("author")
    if not isinstance(author, dict):
        raise _fail("portable_manifest_invalid")
    identity = {
        "plugin_id": portable["name"],
        "version": portable["version"],
        "author": author["name"],
        "description": portable["description"],
        "display_name": interface["displayName"],
        "short_description": interface["shortDescription"],
        "long_description": interface["longDescription"],
        "developer_name": interface["developerName"],
        "category": interface["category"],
        "capabilities": tuple(interface["capabilities"]),
        "default_prompt": (
            tuple(interface["defaultPrompt"])
            if isinstance(interface["defaultPrompt"], list)
            else interface["defaultPrompt"]
        ),
    }
    if compatibility.get("name") != portable.get("name"):
        raise _fail("manifest_pair_mismatch")
    candidate_manifest = _load_json(
        root / "PLUGIN-BUILDER-MANIFEST.json", "candidate_manifest_invalid"
    )
    expected_schema = (
        "plugin-builder-candidate-manifest-v3"
        if metadata.schema.endswith("v3")
        else "plugin-builder-candidate-manifest-v2"
    )
    if candidate_manifest.get("schema") != expected_schema:
        raise _fail("candidate_manifest_invalid")
    preflight_sha256 = sha256(_canonical_bytes(metadata.preflight_evidence)).hexdigest()
    if candidate_manifest.get("preflight_evidence_sha256") != preflight_sha256:
        raise _fail("preflight_evidence_sha256_mismatch")
    tool_bindings = candidate_manifest.get("tool_bindings")
    tool_contracts = candidate_manifest.get("tool_contracts")
    if not isinstance(tool_bindings, list) or not isinstance(tool_contracts, list):
        raise _fail("candidate_manifest_invalid")
    if _canonical_bytes(tool_bindings) != _canonical_bytes(metadata.tool_bindings):
        raise _fail("tool_bindings_mismatch")
    if sha256(_canonical_bytes(tool_contracts)).hexdigest() != metadata.tool_contracts_sha256:
        raise _fail("tool_contracts_sha256_mismatch")
    validated_contracts: list[Mapping[str, object]] = []
    for contract in tool_contracts:
        validated = plugin_authoring.validate_application_tool_contract(contract)
        if validated.errors or validated.blockers:
            raise _fail("tool_contract_invalid", validated.id)
        validated_contracts.append(MappingProxyType(dict(contract)))
    return identity, str(candidate_manifest.get("plan_sha256", "")), tuple(validated_contracts)


def _scan_public_content(root: Path) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    mcp_files = tuple(
        name for name in (".mcp.json", "mcp.json") if (root / name).is_file()
    )
    for relative in mcp_files:
        _load_json(root / relative, "mcp_manifest_invalid")
    dependencies: list[str] = []
    executables: list[str] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if any(part.casefold() in _FORBIDDEN_CREDENTIAL_NAMES for part in path.relative_to(root).parts):
            raise _fail("credential_material_forbidden", relative)
        if path.name in _DEPENDENCY_FILES:
            dependencies.append(relative)
        if path.suffix.casefold() in _EXECUTABLE_SUFFIXES:
            executables.append(relative)
        if path.suffix.casefold() not in {".md", ".json", ".txt", ".py", ".js", ".mjs", ".cjs", ".ps1", ".sh", ".toml", ".yaml", ".yml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            continue
        if path.suffix.casefold() == ".py" and any(
            marker in text for marker in _DEVELOPMENT_IMPORTS
        ):
            raise _fail("development_import_forbidden", relative)
        if _CREDENTIAL.search(text):
            raise _fail("credential_material_forbidden", relative)
        if any(fragment in text for fragment in SECRET_FRAGMENTS) or any(
            pattern.search(text) for pattern in _SECRET_PATTERNS
        ):
            raise _fail("credential_material_forbidden", relative)
    return mcp_files, tuple(dependencies), tuple(executables)


def _inspect_evidence(
    evidence: Path,
    metadata: PackageMetadata,
    *,
    version: str,
    plan_sha256: str,
) -> tuple[str, Mapping[str, str]]:
    try:
        inventory = plugin_authoring.inventory_archive(evidence)
    except plugin_authoring.PluginAuthoringError as exc:
        raise _fail(f"evidence_{exc.code}") from exc
    with tempfile.TemporaryDirectory(prefix="plugin-onboarding-evidence-") as name:
        extracted = Path(name) / "bundle"
        try:
            plugin_authoring.extract_archive(evidence, extracted)
        except plugin_authoring.PluginAuthoringError as exc:
            raise _fail(f"evidence_{exc.code}") from exc
        index = _load_json(extracted / "evidence-index.json", "evidence_index_invalid")
        if set(index) != {"schema", "result", "evidence"} or index.get("schema") != "plugin-builder-runtime-evidence-index-v1":
            raise _fail("evidence_index_invalid")
        result_record = index.get("result")
        if not isinstance(result_record, dict) or set(result_record) != {"path", "sha256", "size"}:
            raise _fail("evidence_index_invalid")
        result_path = result_record.get("path")
        if not isinstance(result_path, str) or "\\" in result_path or ".." in result_path.split("/"):
            raise _fail("evidence_result_path_invalid")
        candidate = extracted.joinpath(*result_path.split("/"))
        try:
            result_bytes = candidate.read_bytes()
        except OSError as exc:
            raise _fail("evidence_result_missing") from exc
        if (
            len(result_bytes) != result_record.get("size")
            or sha256(result_bytes).hexdigest() != result_record.get("sha256")
        ):
            raise _fail("evidence_result_identity_mismatch")
        result = _load_json(candidate, "evidence_result_invalid")
        required = {
            "schema", "plugin_id", "version", "zip_sha256",
            "member_manifest_sha256", "candidate_sha256", "verification_sha256",
            "plan_sha256", "session_sha256", "operation_identities", "evidence_states",
        }
        if set(result) != required or result.get("schema") != "plugin-onboarding-runtime-observations-v1":
            raise _fail("evidence_result_invalid")
        expected = {
            "plugin_id": metadata.plugin_id,
            "version": version,
            "zip_sha256": metadata.archive_sha256,
            "member_manifest_sha256": metadata.member_manifest_sha256,
            "candidate_sha256": metadata.candidate_sha256,
            "verification_sha256": metadata.verification_sha256,
            "plan_sha256": plan_sha256,
        }
        for field, value in expected.items():
            if result.get(field) != value:
                raise _fail(f"evidence_{field}_mismatch")
        session_sha = result.get("session_sha256")
        if not isinstance(session_sha, str) or not _DIGEST.fullmatch(session_sha):
            raise _fail("evidence_session_sha256_invalid")
        operations = result.get("operation_identities")
        if not isinstance(operations, list):
            raise _fail("evidence_operation_identities_invalid")
        expected_operations = {
            (str(item.get("tool_id", "")), str(item.get("contract_sha256", "")))
            for item in metadata.tool_bindings
        }
        observed_operations = {
            (str(item.get("operation_id", "")), str(item.get("sha256", "")))
            for item in operations if isinstance(item, dict)
        }
        if observed_operations != expected_operations:
            raise _fail("evidence_operation_identities_mismatch")
        states = result.get("evidence_states")
        if not isinstance(states, dict) or set(states) != set(_EVIDENCE_LAYERS):
            raise _fail("evidence_states_invalid")
        if any(value not in {"RUNTIME VERIFIED", "NOT VERIFIED", "NOT APPLICABLE"} for value in states.values()):
            raise _fail("evidence_states_invalid")
        if "RUNTIME VERIFIED" in states.values():
            raise _fail("evidence_session_identity_unverifiable")
        expected_members = {
            "evidence-index.json",
            result_path,
            *(str(item.get("path")) for item in index["evidence"] if isinstance(item, dict)),
        }
        if {member.path for member in inventory.members} != expected_members:
            raise _fail("evidence_members_unindexed")
        return "STATICALLY VERIFIED", MappingProxyType(dict(states))


def inspect_plugin_builder_package(
    archive: Path,
    metadata: PackageMetadata,
    *,
    evidence: Path | None = None,
) -> OnboardingInspection:
    """Inspect a Plugin Builder package without executing imported content."""

    try:
        inventory = plugin_authoring.inventory_archive(Path(archive))
    except plugin_authoring.PluginAuthoringError as exc:
        raise _fail(exc.code, exc.detail) from exc
    _validate_metadata_closure(inventory, metadata)
    with tempfile.TemporaryDirectory(prefix="plugin-onboarding-") as name:
        extracted = Path(name) / "archive"
        try:
            plugin_authoring.extract_archive(Path(archive), extracted)
            located = plugin_authoring.locate_plugin_archive_root(extracted)
        except plugin_authoring.PluginAuthoringError as exc:
            raise _fail(exc.code, exc.detail) from exc
        if located.profile != "PORTABLE_SINGLE_DIRECTORY":
            raise _fail("envelope_profile_mismatch")
        actual_candidate = plugin_authoring.tree_manifest(located.path)
        if tuple(map(_member_tuple, actual_candidate)) != tuple(
            map(_member_tuple, metadata.candidate_members)
        ):
            raise _fail("candidate_members_mismatch")
        if plugin_authoring.tree_sha256(located.path) != metadata.candidate_sha256:
            raise _fail("candidate_sha256_mismatch")
        identity, plan_sha, tool_contracts = _manifest_identity(located.path, metadata)
        mcp_files, dependency_files, executable_files = _scan_public_content(located.path)
        if evidence is None:
            evidence_state = "NOT VERIFIED"
            evidence_states: Mapping[str, str] = MappingProxyType(
                {layer: "NOT VERIFIED" for layer in _EVIDENCE_LAYERS}
            )
        else:
            evidence_state, evidence_states = _inspect_evidence(
                Path(evidence), metadata, version=str(identity["version"]), plan_sha256=plan_sha
            )
        return OnboardingInspection(
            schema="plugin-onboarding-inspection-v1",
            plugin_id=metadata.plugin_id,
            version=str(identity["version"]),
            package_state="STATICALLY VERIFIED",
            archive_sha256=metadata.archive_sha256,
            candidate_sha256=metadata.candidate_sha256,
            verification_sha256=metadata.verification_sha256,
            content_tree_sha256=metadata.candidate_sha256,
            member_manifest_sha256=metadata.member_manifest_sha256,
            members=metadata.members,
            candidate_members=metadata.candidate_members,
            manifest_profile=metadata.manifest_profile,
            manifest_identity=MappingProxyType(identity),
            preflight_evidence=metadata.preflight_evidence,
            preflight_evidence_sha256=sha256(
                _canonical_bytes(metadata.preflight_evidence)
            ).hexdigest(),
            command_evidence=metadata.command_evidence,
            fallback_activations=metadata.fallback_activations,
            producer_evidence_states=metadata.evidence_states,
            tool_bindings=metadata.tool_bindings,
            tool_contracts_sha256=metadata.tool_contracts_sha256,
            tool_contracts=tool_contracts,
            offline_validator_files=(),
            mcp_files=mcp_files,
            dependency_files=dependency_files,
            executable_files=executable_files,
            executed_files=(),
            runtime_realization_state=metadata.runtime_realization_state or "NOT VERIFIED",
            capabilities_sha256=metadata.capabilities_sha256,
            realizations_sha256=metadata.realizations_sha256,
            adapter_registry_sha256=metadata.adapter_registry_sha256,
            generated_runtime_configuration_sha256=metadata.generated_runtime_configuration_sha256,
            runtime_realizations=metadata.runtime_realizations,
            evidence_states=evidence_states,
            evidence_bundle_state=evidence_state,
            input_profile=metadata.schema.upper().replace("-", "_"),
            producer_claims=MappingProxyType({"schema": metadata.schema}),
        )


def _flat_manifest_identity(root: Path) -> dict[str, object]:
    portable = _load_json(root / "plugin.json", "portable_manifest_invalid")
    compatibility = _load_json(
        root / ".codex-plugin" / "plugin.json", "compatibility_manifest_invalid"
    )
    if plugin_authoring.manifest_pair_mismatches(portable, compatibility):
        raise _fail("manifest_pair_mismatch")
    extensions = portable.get("extensions")
    openai = extensions.get("com.openai") if isinstance(extensions, dict) else None
    interface = openai.get("interface") if isinstance(openai, dict) else None
    author = portable.get("author")
    if not isinstance(interface, dict) or not isinstance(author, dict):
        raise _fail("portable_manifest_invalid")
    return {
        "plugin_id": portable.get("name"),
        "version": portable.get("version"),
        "author": author.get("name"),
        "description": portable.get("description"),
        "display_name": interface.get("displayName"),
        "short_description": interface.get("shortDescription"),
        "long_description": interface.get("longDescription"),
        "developer_name": interface.get("developerName"),
        "category": interface.get("category"),
        "capabilities": tuple(interface.get("capabilities", ())),
        "default_prompt": (
            tuple(interface.get("defaultPrompt", ()))
            if isinstance(interface.get("defaultPrompt"), list)
            else interface.get("defaultPrompt")
        ),
    }


def inspect_legacy_plugin_archive(archive: Path) -> OnboardingInspection:
    """Inspect a legacy or Workbench-repaired flat archive without mutation."""

    try:
        inventory = plugin_authoring.inventory_archive(Path(archive))
    except plugin_authoring.PluginAuthoringError as exc:
        raise _fail(exc.code, exc.detail) from exc
    with tempfile.TemporaryDirectory(prefix="plugin-onboarding-legacy-") as name:
        extracted = Path(name) / "archive"
        try:
            plugin_authoring.extract_archive(Path(archive), extracted)
            located = plugin_authoring.locate_plugin_archive_root(extracted)
        except plugin_authoring.PluginAuthoringError as exc:
            raise _fail(exc.code, exc.detail) from exc
        if located.profile != "LEGACY_FLAT":
            raise _fail("envelope_profile_mismatch")
        legacy_path = located.path / "PLUGIN-BUILDER-MANIFEST.json"
        repair_path = located.path / "WORKBENCH-REPAIR-MANIFEST.json"
        if legacy_path.is_file() and repair_path.is_file():
            raise _fail("authority_ambiguous")
        if legacy_path.is_file():
            authority = _load_json(legacy_path, "legacy_manifest_invalid")
            if authority.get("schema") != "plugin-builder-candidate-manifest-v1":
                raise _fail("legacy_manifest_invalid")
            input_profile = "PLUGIN_BUILDER_CANDIDATE_V1"
            producer_claims = {
                key: authority[key]
                for key in ("schema", "candidate_version", "w1_state", "w2_state")
                if key in authority
            }
        elif repair_path.is_file():
            authority = _load_json(repair_path, "repair_manifest_invalid")
            if authority.get("schema") != "workbench-repair-manifest-v1":
                raise _fail("repair_manifest_invalid")
            input_profile = "WORKBENCH_REPAIRED_PLUGIN_V1"
            producer_claims = {
                "schema": "plugin-builder-candidate-manifest-v1",
                "verification_state": "NOT VERIFIED",
                "source_archive_sha256": authority.get("source_archive_sha256"),
            }
        else:
            raise _fail("authority_unknown")
        identity = _flat_manifest_identity(located.path)
        plugin_id = identity.get("plugin_id")
        version = identity.get("version")
        if not isinstance(plugin_id, str) or not isinstance(version, str):
            raise _fail("portable_manifest_invalid")
        tree_members = plugin_authoring.tree_manifest(located.path)
        content_tree_sha256 = plugin_authoring.tree_sha256(located.path)
        issues = plugin_authoring.validate_plugin_tree(located.path)
        mcp_files, dependency_files, executable_files = _scan_public_content(located.path)
        evidence_states = MappingProxyType(
            {layer: "NOT VERIFIED" for layer in _EVIDENCE_LAYERS}
        )
        return OnboardingInspection(
            schema="plugin-onboarding-inspection-v1",
            plugin_id=plugin_id,
            version=version,
            package_state="STATICALLY VERIFIED" if not issues else "NOT VERIFIED",
            archive_sha256=inventory.archive_sha256,
            candidate_sha256=None,
            verification_sha256=None,
            content_tree_sha256=content_tree_sha256,
            member_manifest_sha256=sha256(
                _canonical_bytes([asdict(member) for member in inventory.members])
            ).hexdigest(),
            members=tuple(
                PackageMember(member.path, member.size, member.sha256)
                for member in inventory.members
            ),
            candidate_members=tree_members,
            manifest_profile="PORTABLE_WITH_OPENAI_COMPATIBILITY",
            manifest_identity=MappingProxyType(identity),
            preflight_evidence=MappingProxyType({}),
            preflight_evidence_sha256=sha256(_canonical_bytes({})).hexdigest(),
            command_evidence=(),
            fallback_activations=(),
            producer_evidence_states=MappingProxyType({"verification": "NOT VERIFIED"}),
            tool_bindings=(),
            tool_contracts_sha256=sha256(_canonical_bytes([])).hexdigest(),
            tool_contracts=(),
            offline_validator_files=(),
            mcp_files=mcp_files,
            dependency_files=dependency_files,
            executable_files=executable_files,
            executed_files=(),
            runtime_realization_state="NOT VERIFIED",
            capabilities_sha256=None,
            realizations_sha256=None,
            adapter_registry_sha256=None,
            generated_runtime_configuration_sha256=None,
            runtime_realizations=(),
            evidence_states=evidence_states,
            evidence_bundle_state="NOT VERIFIED",
            input_profile=input_profile,
            producer_claims=MappingProxyType(producer_claims),
            diagnostics=tuple(
                f"{issue.code}:{issue.path}" for issue in issues
            ),
        )


def inspect_workbench_repaired_package(
    archive: Path,
    metadata: WorkbenchRepairMetadata,
) -> OnboardingInspection:
    """Close Workbench repair metadata against current archive bytes."""

    inspected = inspect_legacy_plugin_archive(archive)
    if inspected.input_profile != "WORKBENCH_REPAIRED_PLUGIN_V1":
        raise _fail("input_profile_mismatch")
    if inspected.archive_sha256 != metadata.archive_sha256:
        raise _fail("archive_sha256_mismatch")
    if inspected.member_manifest_sha256 != metadata.member_manifest_sha256:
        raise _fail("member_manifest_sha256_mismatch")
    if inspected.content_tree_sha256 != metadata.content_tree_sha256:
        raise _fail("content_tree_sha256_mismatch")
    if tuple(map(_member_tuple, inspected.members)) != tuple(
        map(_member_tuple, metadata.members)
    ):
        raise _fail("archive_members_mismatch")
    if inspected.plugin_id != metadata.plugin_id or inspected.version != metadata.version:
        raise _fail("plugin_identity_mismatch")
    repair_member = next(
        (member for member in inspected.members if member.path == "WORKBENCH-REPAIR-MANIFEST.json"),
        None,
    )
    if repair_member is None or repair_member.sha256 != metadata.repair_manifest_sha256:
        raise _fail("repair_manifest_sha256_mismatch")
    try:
        with zipfile.ZipFile(archive, "r") as package:
            repair_payload = json.loads(
                package.read("WORKBENCH-REPAIR-MANIFEST.json").decode("utf-8")
            )
    except (OSError, KeyError, UnicodeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        raise _fail("repair_manifest_invalid") from exc
    if not isinstance(repair_payload, dict) or repair_payload.get("schema") != "workbench-repair-manifest-v1":
        raise _fail("repair_manifest_invalid")
    if repair_payload.get("source_archive_sha256") != metadata.source_archive_sha256:
        raise _fail("source_archive_sha256_mismatch")
    if (
        repair_payload.get("plugin_id") != metadata.plugin_id
        or repair_payload.get("target_version") != metadata.version
    ):
        raise _fail("repair_manifest_identity_mismatch")
    validated_contracts: tuple[Mapping[str, object], ...] = ()
    tool_bindings: tuple[Mapping[str, object], ...] = ()
    tool_contracts_sha256 = sha256(_canonical_bytes([])).hexdigest()
    offline_validator_files: tuple[str, ...] = ()
    if metadata.schema == "workbench-repaired-plugin-v2":
        raw_contracts = repair_payload.get("tool_contracts")
        raw_bindings = repair_payload.get("tool_bindings")
        raw_offline_validators = repair_payload.get("offline_validators")
        if (
            not isinstance(raw_contracts, list)
            or not isinstance(raw_bindings, list)
            or not isinstance(raw_offline_validators, list)
        ):
            raise _fail("repair_tool_declarations_invalid")
        if _canonical_bytes(raw_bindings) != _canonical_bytes(metadata.tool_bindings):
            raise _fail("tool_bindings_mismatch")
        computed_contracts_sha256 = sha256(_canonical_bytes(raw_contracts)).hexdigest()
        if computed_contracts_sha256 != metadata.tool_contracts_sha256:
            raise _fail("tool_contracts_sha256_mismatch")
        contracts_by_id: dict[str, Mapping[str, object]] = {}
        validated: list[Mapping[str, object]] = []
        for contract in raw_contracts:
            result = plugin_authoring.validate_application_tool_contract(contract)
            if result.errors or result.blockers or not isinstance(contract, dict):
                raise _fail("tool_contract_invalid", result.id)
            contracts_by_id[result.id] = contract
            validated.append(MappingProxyType(dict(contract)))
        binding_ids: set[str] = set()
        for binding in raw_bindings:
            if not isinstance(binding, dict):
                raise _fail("tool_binding_invalid")
            tool_id = binding.get("tool_id")
            contract = contracts_by_id.get(tool_id) if isinstance(tool_id, str) else None
            if (
                contract is None
                or binding.get("contract_sha256")
                != sha256(_canonical_bytes(contract)).hexdigest()
                or tool_id in binding_ids
            ):
                raise _fail("tool_binding_invalid", str(tool_id or ""))
            binding_ids.add(tool_id)
        if binding_ids != set(contracts_by_id):
            raise _fail("tool_binding_invalid")
        validated_contracts = tuple(validated)
        tool_bindings = metadata.tool_bindings
        tool_contracts_sha256 = computed_contracts_sha256
        if _canonical_bytes(raw_offline_validators) != _canonical_bytes(
            metadata.offline_validators
        ):
            raise _fail("offline_validators_mismatch")
        if (
            sha256(_canonical_bytes(raw_offline_validators)).hexdigest()
            != metadata.offline_validators_sha256
        ):
            raise _fail("offline_validators_sha256_mismatch")
        offline_ids: set[str] = set()
        offline_files: set[str] = set()
        for validator in raw_offline_validators:
            if not isinstance(validator, dict) or set(validator) != {
                "id",
                "files",
                "runtime_role",
                "required",
                "installed_runtime_callable",
                "source_contract_sha256",
            }:
                raise _fail("offline_validator_invalid")
            validator_id = validator.get("id")
            files = validator.get("files")
            source_digest = validator.get("source_contract_sha256")
            if (
                not isinstance(validator_id, str)
                or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", validator_id) is None
                or validator_id in offline_ids
                or not isinstance(files, list)
                or not files
                or validator.get("runtime_role") != "OFFLINE_PACKAGE_VALIDATION_ONLY"
                or validator.get("required") is not False
                or validator.get("installed_runtime_callable") is not False
                or not isinstance(source_digest, str)
                or _DIGEST.fullmatch(source_digest) is None
            ):
                raise _fail("offline_validator_invalid", str(validator_id or ""))
            offline_ids.add(validator_id)
            for relative in files:
                if (
                    not isinstance(relative, str)
                    or PurePosixPath(relative).is_absolute()
                    or any(part in {"", ".", ".."} for part in PurePosixPath(relative).parts)
                    or relative not in {member.path for member in metadata.members}
                ):
                    raise _fail("offline_validator_file_invalid", str(relative))
                offline_files.add(relative)
        offline_validator_files = tuple(sorted(offline_files))
    for field, validation in (
        ("extracted_validation", metadata.extracted_validation),
        ("safety_validation", metadata.safety_validation),
    ):
        if set(validation) != {"state", "diagnostics"} or validation.get("state") != "PASS" or validation.get("diagnostics") not in ((), []):
            raise _fail(f"{field}_invalid")
    if inspected.diagnostics:
        raise _fail("plugin_tree_invalid", inspected.diagnostics[0])
    return replace(
        inspected,
        producer_claims=metadata.producer_claims,
        producer_evidence_states=metadata.evidence_states,
        tool_bindings=tool_bindings,
        tool_contracts_sha256=tool_contracts_sha256,
        tool_contracts=validated_contracts,
        offline_validator_files=offline_validator_files,
        input_profile=metadata.schema.upper().replace("-", "_"),
    )


def inspection_payload(inspection: OnboardingInspection) -> dict[str, object]:
    """Return a path-independent JSON payload for an inspection observation."""

    return {
        "schema": inspection.schema,
        "plugin_id": inspection.plugin_id,
        "version": inspection.version,
        "input_profile": inspection.input_profile,
        "package_state": inspection.package_state,
        "archive_sha256": inspection.archive_sha256,
        "content_tree_sha256": inspection.content_tree_sha256,
        "member_manifest_sha256": inspection.member_manifest_sha256,
        "members": [asdict(member) for member in inspection.members],
        "producer_claims": _json_value(inspection.producer_claims),
        "producer_evidence_states": _json_value(inspection.producer_evidence_states),
        "evidence_states": dict(inspection.evidence_states),
        "diagnostics": list(inspection.diagnostics),
    }
