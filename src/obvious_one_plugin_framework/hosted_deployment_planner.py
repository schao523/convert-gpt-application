"""Deterministic planning and validation for hosted deployment archives."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Mapping

from .content_policy import (
    ContentPolicyError,
    ResolvedContentPolicy,
    canonical_content_bytes,
    resolve_content_policies,
)
from .contract import DistributionContract, load_contract
from .hosted_deployment_contract import (
    DeploymentMapping,
    HostedDeploymentContract,
    HostedDeploymentError,
)
from .results import ArtifactRecord, Diagnostic, MutationRecord, OperationResult
from .verification import VerificationConfigError, load_application_config_path


_OPERATIONS = frozenset({"OPENAI_HOSTED_CREATE", "OPENAI_HOSTED_UPDATE"})
_FORBIDDEN_NAMES = frozenset({".env", "credentials.json", "id_rsa", "id_dsa"})
_SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\bsk-[A-Za-z0-9_-]{16,}\b"),
)


@dataclass(frozen=True)
class HostedDeploymentPlan:
    proposal: Mapping[str, object]
    unresolved_codes: tuple[str, ...]


@dataclass(frozen=True)
class HostedDeploymentValidation:
    contract: HostedDeploymentContract
    archive_paths: tuple[str, ...]
    content_policies: Mapping[str, ResolvedContentPolicy]
    source_paths: Mapping[str, Path]
    local_capabilities: Mapping[str, str]
    hosted_capabilities: Mapping[str, str]
    declared_channels: Mapping[str, str]
    generated_channels: Mapping[str, str]


def _is_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & 0x400)


def _safe_files(root: Path, relative: str, *, require_directory: bool = False) -> tuple[tuple[str, Path], ...]:
    resolved_root = root.resolve()
    base = root / Path(relative)
    current = resolved_root
    for part in Path(relative).parts:
        current = current / part
        if _is_link(current):
            raise HostedDeploymentError("link_forbidden", relative)
    if require_directory:
        if not base.is_dir():
            raise HostedDeploymentError("mapped_source_missing", relative)
        candidates = sorted((item for item in base.rglob("*") if item.is_file()), key=lambda item: item.as_posix())
    else:
        if not base.is_file():
            raise HostedDeploymentError("mapped_source_missing", relative)
        candidates = [base]
    result: list[tuple[str, Path]] = []
    for candidate in candidates:
        source_relative = candidate.relative_to(root).as_posix()
        current = resolved_root
        for part in Path(source_relative).parts:
            current = current / part
            if _is_link(current):
                raise HostedDeploymentError("link_forbidden", source_relative)
        resolved = candidate.resolve(strict=True)
        if not resolved.is_relative_to(resolved_root):
            raise HostedDeploymentError("mapped_source_escape", source_relative)
        result.append((source_relative, candidate))
    return tuple(result)


def _selected_canonical_files(contract: DistributionContract) -> tuple[tuple[str, Path], ...]:
    selected: dict[str, Path] = {}
    excluded = set(contract.exclude_paths)
    for relative in contract.include_files:
        for item, path in _safe_files(contract.source_root, relative):
            selected[item] = path
    for prefix in contract.include_prefixes:
        for item, path in _safe_files(contract.source_root, prefix, require_directory=True):
            if item not in excluded:
                selected[item] = path
    for relative in excluded:
        selected.pop(relative, None)
    return tuple((key, selected[key]) for key in sorted(selected))


def _diagnostic(code: str, path: str | None = None, candidates: tuple[str, ...] = ()) -> Diagnostic:
    return Diagnostic(code=code, path=path, message=code.replace("_", " "), candidates=candidates)


def _build_plan(application, operation: str) -> HostedDeploymentPlan:
    if operation not in _OPERATIONS:
        raise HostedDeploymentError("invalid_operation", operation)
    distribution = load_contract(application.distribution_contract)
    if distribution.schema_version != 3:
        raise HostedDeploymentError("legacy_contract_read_only", str(distribution.schema_version))
    selected = _selected_canonical_files(distribution)
    diagnostics: list[Diagnostic] = []
    policies: Mapping[str, ResolvedContentPolicy] = {}
    try:
        policies = resolve_content_policies(distribution, [relative for relative, _ in selected])
    except ContentPolicyError as exc:
        diagnostics.append(_diagnostic(exc.code, exc.paths[0] if exc.paths else None, exc.candidates))

    candidates: list[dict[str, object]] = []
    canonical_targets: set[str] = set()
    for relative, _ in selected:
        policy = policies.get(relative)
        candidates.append({
            "id": "canonical-" + re.sub(r"[^a-z0-9]+", "-", relative.lower()).strip("-"),
            "source_kind": "canonical_application",
            "source": relative,
            "target": relative,
            "copy_mode": "copy_file",
            "classification": policy.classification if policy else "UNRESOLVED",
            "redistribution_reference": policy.rule_id if policy else None,
        })
        canonical_targets.add(relative.casefold())

    adapter_root = application.root / "hosted-openai" / "adapter"
    if adapter_root.is_dir():
        for source_relative, _ in _safe_files(application.root / "hosted-openai", "adapter", require_directory=True):
            target = source_relative.removeprefix("adapter/")
            candidates.append({
                "id": "adapter-" + re.sub(r"[^a-z0-9]+", "-", target.lower()).strip("-"),
                "source_kind": "hosted_adapter",
                "source": source_relative,
                "target": target,
                "copy_mode": "copy_file",
                "classification": "UNRESOLVED",
                "redistribution_reference": None,
            })
            diagnostics.append(_diagnostic("adapter_rights_unresolved", source_relative, ("text", "binary", "exclude")))
            if target.casefold() in canonical_targets or (
                target.startswith("skills/")
                and any(item.startswith("skills/" + target.split("/", 2)[1] + "/") for item in canonical_targets)
            ):
                diagnostics.append(_diagnostic("adapter_duplicates_canonical_content", target))

    if operation == "OPENAI_HOSTED_UPDATE":
        diagnostics.append(_diagnostic("hosted_identity_required", "hosted-openai/hosted-identity.json"))
    required_inputs = ["capabilities", "channel_status", "hosted_lineage", "target_mappings", "target_version"]
    if operation == "OPENAI_HOSTED_UPDATE":
        required_inputs.append("hosted_identity")
    proposal = {
        "proposal_schema": "hosted-deployment-proposal-v1",
        "application_id": application.application_id,
        "operation": operation,
        "required_inputs": sorted(required_inputs),
        "candidate_mappings": sorted(candidates, key=lambda item: (str(item["target"]).casefold(), str(item["source"]))),
        "unresolved_codes": sorted({item.code for item in diagnostics} | {"hosted_deployment_decisions_required"}),
    }
    return HostedDeploymentPlan(proposal=proposal, unresolved_codes=tuple(proposal["unresolved_codes"]))


def _write_new_json(destination: Path, payload: Mapping[str, object]) -> bool:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return False
    content = (json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=f".{destination.name}.", suffix=".tmp", delete=False) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name
        try:
            os.link(temporary_name, destination)
        except FileExistsError:
            return False
        return True
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def plan_hosted_deployment(application_path: Path, operation: str, output: Path) -> OperationResult:
    destination = Path(output)
    if destination.exists():
        return OperationResult("plan-hosted-deployment", "FAIL", "hosted_deployment_proposal_exists")
    config_path = Path(application_path).resolve()
    if config_path.is_dir():
        config_path = config_path / "conversion.json"
    try:
        application = load_application_config_path(config_path, config_path.parent)
    except VerificationConfigError as exc:
        raise HostedDeploymentError("invalid_application_config", str(exc)) from exc
    plan = _build_plan(application, operation)
    if not _write_new_json(destination, plan.proposal):
        return OperationResult("plan-hosted-deployment", "FAIL", "hosted_deployment_proposal_exists")
    content = destination.read_bytes()
    diagnostics = tuple(_diagnostic(code) for code in plan.unresolved_codes if code != "hosted_deployment_decisions_required")
    return OperationResult(
        "plan-hosted-deployment",
        "BLOCKED",
        "hosted_deployment_decisions_required",
        diagnostics=diagnostics,
        artifacts=(ArtifactRecord(destination.name, "hosted_deployment_proposal", sha256(content).hexdigest(), len(content)),),
        mutations=(MutationRecord(destination.name, "created"),),
        evidence={"application_id": application.application_id, "operation": operation},
    )


def _expand_mapping(contract: HostedDeploymentContract, mapping: DeploymentMapping) -> tuple[tuple[str, str, Path], ...]:
    if mapping.source_kind == "canonical_application":
        root = contract.application_root
    else:
        root = contract.contract_path.parent
    files = _safe_files(root, mapping.source, require_directory=mapping.copy_mode == "copy_tree")
    expanded: list[tuple[str, str, Path]] = []
    for source_relative, source in files:
        if mapping.copy_mode == "copy_tree":
            suffix = source.relative_to(root / mapping.source).as_posix()
            target = f"{mapping.target.rstrip('/')}/{suffix}"
        else:
            target = mapping.target
        expanded.append((source_relative, target, source))
    return tuple(expanded)


def _manifest(path: Path, label: str) -> Mapping[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HostedDeploymentError("hosted_manifest_invalid", label) from exc
    if not isinstance(value, dict):
        raise HostedDeploymentError("hosted_manifest_invalid", label)
    return value


def _adapter_evidence(contract: HostedDeploymentContract, reference: str) -> None:
    text = reference.replace("\\", "/")
    candidate = (contract.contract_path.parent / text).resolve()
    if not candidate.is_relative_to(contract.application_root) or not candidate.is_file():
        raise HostedDeploymentError("rights_unresolved", reference)


def _forbidden(path: str) -> bool:
    parts = [part.casefold() for part in Path(path).parts]
    return any(part in _FORBIDDEN_NAMES or part.endswith((".pem", ".key")) for part in parts)


def validate_hosted_deployment(contract: HostedDeploymentContract) -> HostedDeploymentValidation:
    selected = {relative for relative, _ in _selected_canonical_files(contract.distribution)}
    source_paths: dict[str, Path] = {}
    policies: dict[str, ResolvedContentPolicy] = {}
    source_kinds: dict[str, str] = {}
    adapter_skill_roots: set[str] = set()

    for mapping in contract.canonical_mappings + contract.adapter_mappings:
        expanded = _expand_mapping(contract, mapping)
        for source_relative, target, source in expanded:
            folded = target.casefold()
            if folded in {item.casefold() for item in source_paths}:
                raise HostedDeploymentError("target_path_collision", target)
            if _forbidden(target):
                raise HostedDeploymentError("forbidden_archive_path", target)
            if mapping.source_kind == "canonical_application":
                if source_relative not in selected:
                    raise HostedDeploymentError("canonical_source_not_selected", source_relative)
                try:
                    source_policy = resolve_content_policies(contract.distribution, [source_relative])[source_relative]
                except ContentPolicyError as exc:
                    raise HostedDeploymentError(exc.code, exc.detail) from exc
                if source_policy.classification != mapping.classification:
                    raise HostedDeploymentError("mapping_classification_mismatch", target)
                if source_policy.rule_id != mapping.redistribution_reference:
                    raise HostedDeploymentError("rights_reference_mismatch", target)
                policy = ResolvedContentPolicy(target, source_policy.classification, source_policy.canonicalization, source_policy.rule_id)
            else:
                _adapter_evidence(contract, mapping.redistribution_reference)
                policy = ResolvedContentPolicy(
                    target,
                    mapping.classification,
                    "utf8-lf" if mapping.classification == "text" else "exact",
                    mapping.redistribution_reference,
                )
                if target.startswith("skills/"):
                    parts = target.split("/")
                    if len(parts) >= 2:
                        adapter_skill_roots.add(parts[1])
            source_paths[target] = source
            policies[target] = policy
            source_kinds[target] = mapping.source_kind

    archive_paths = tuple(sorted(source_paths))
    for skill in adapter_skill_roots:
        if skill not in set(contract.explicit_only_skills):
            raise HostedDeploymentError("adapter_duplicates_canonical_content", skill)

    manifest_requirements = {
        "plugin.json": contract.portable_manifest,
        ".codex-plugin/plugin.json": contract.legacy_manifest,
    }
    for target, declared_source in manifest_requirements.items():
        if target not in source_paths:
            code = "portable_manifest_missing" if target == "plugin.json" else "legacy_manifest_missing"
            raise HostedDeploymentError(code)
        expected = (contract.contract_path.parent / declared_source).resolve()
        if source_paths[target].resolve() != expected:
            raise HostedDeploymentError("hosted_manifest_mapping_mismatch", target)
    portable = _manifest(source_paths["plugin.json"], "plugin.json")
    legacy = _manifest(source_paths[".codex-plugin/plugin.json"], ".codex-plugin/plugin.json")
    for manifest in (portable, legacy):
        if manifest.get("name") != contract.package_name or manifest.get("version") != contract.target_version:
            raise HostedDeploymentError("hosted_manifest_identity_mismatch")

    discovered_skills = {
        path.split("/")[1]
        for path in archive_paths
        if path.startswith("skills/") and path.count("/") >= 2 and path.endswith("/SKILL.md")
    }
    if discovered_skills != set(contract.expected_skills):
        raise HostedDeploymentError("expected_skill_mismatch")
    for skill in contract.explicit_only_skills:
        policy_path = f"skills/{skill}/agents/openai.yaml"
        if policy_path not in source_paths:
            raise HostedDeploymentError("explicit_only_policy_missing", skill)
        try:
            policy_text = source_paths[policy_path].read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise HostedDeploymentError("explicit_only_policy_missing", skill) from exc
        if "allow_implicit_invocation: false" not in policy_text:
            raise HostedDeploymentError("explicit_only_policy_missing", skill)

    total_bytes = 0
    for target in archive_paths:
        try:
            content = canonical_content_bytes(source_paths[target], policies[target])
        except (OSError, ContentPolicyError) as exc:
            code = exc.code if isinstance(exc, ContentPolicyError) else "mapped_source_read_failed"
            raise HostedDeploymentError(code, target) from exc
        if any(pattern.search(content) for pattern in _SECRET_PATTERNS):
            raise HostedDeploymentError("secret_detected", target)
        total_bytes += len(content)
        if total_bytes > contract.max_archive_bytes:
            raise HostedDeploymentError("hosted_archive_size_limit")

    local_capabilities: dict[str, str] = {}
    hosted_capabilities: dict[str, str] = {}
    for capability in contract.capabilities:
        for artifact in capability.artifact_paths:
            if artifact not in source_paths:
                raise HostedDeploymentError("required_capability_artifact_missing", capability.capability_id)
        if capability.fallback is not None:
            _adapter_evidence(contract, capability.fallback.approval_reference)
            for artifact in capability.fallback.artifact_paths:
                if artifact not in source_paths:
                    raise HostedDeploymentError("fallback_artifact_missing", capability.capability_id)
        local_capabilities[capability.capability_id] = (
            "NOT VERIFIED" if capability.local_verification_test is not None else "NOT APPLICABLE"
        )
        hosted_capabilities[capability.capability_id] = "NOT VERIFIED"

    declared_channels = {key: value.status for key, value in contract.channels.items()}
    generated_channels = dict(declared_channels)
    generated_channels["openai_hosted"] = "PENDING_ACTION"
    return HostedDeploymentValidation(
        contract=contract,
        archive_paths=archive_paths,
        content_policies=policies,
        source_paths=source_paths,
        local_capabilities=local_capabilities,
        hosted_capabilities=hosted_capabilities,
        declared_channels=declared_channels,
        generated_channels=generated_channels,
    )
