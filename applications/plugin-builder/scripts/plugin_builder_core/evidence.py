"""Validate and package digest-addressed installed-runtime evidence."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

from .bootstrap import plugin_authoring
from .implementation_plan import canonical_bytes
from .runtime_adapters import adapter_registry


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_STATES = {"EXPECTED", "STATICALLY VERIFIED", "RUNTIME VERIFIED", "NOT VERIFIED", "NOT APPLICABLE"}
_RESULTS = {"PASS", "FAIL", "NOT VERIFIED", "NOT APPLICABLE"}
_RUNTIMES = {"Codex", "ChatGPT Work Local/Desktop"}
_KINDS = {"BUNDLED_LOCAL", "FRAMEWORK_ADAPTER", "RUNTIME_NATIVE", "MCP_ADAPTER"}
_PRIVATE_VALUE = re.compile(r"(?i)(?:bearer\s+\S+|(?:api[_-]?key|secret|token|password|credential)\s*[:=]\s*\S+|sk-[a-z0-9]{16,})")


@dataclass(frozen=True)
class EvidenceBundleOutcome:
    status: str
    errors: tuple[str, ...]
    archive_sha256: str | None = None
    result_sha256: str | None = None
    index_sha256: str | None = None


def _exact(value: object, keys: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == keys


def _digest(value: object) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _contains_private_value(value: object) -> bool:
    if isinstance(value, str):
        return _PRIVATE_VALUE.search(value) is not None
    if isinstance(value, list):
        return any(_contains_private_value(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_private_value(item) for item in value.values())
    return False


def _validate_runtime_result_v1(payload: object) -> tuple[str, ...]:
    errors: list[str] = []
    root_keys = {"schema", "runtime", "artifact", "scenarios", "tools", "overall_state"}
    if not _exact(payload, root_keys):
        return ("result.invalid_object",)
    assert isinstance(payload, dict)
    if payload.get("schema") != "plugin-builder-runtime-result-v1":
        errors.append("result.schema_invalid")
    runtime = payload.get("runtime")
    runtime_keys = {"name", "version", "os", "clean_workspace", "discovery_observed", "repository_absent"}
    if not _exact(runtime, runtime_keys):
        errors.append("result.runtime_invalid")
    else:
        assert isinstance(runtime, dict)
        if runtime.get("name") not in _RUNTIMES or not isinstance(runtime.get("version"), str) or not runtime["version"] or not isinstance(runtime.get("os"), str) or not runtime["os"]:
            errors.append("result.runtime_identity_invalid")
        if any(type(runtime.get(key)) is not bool for key in ("clean_workspace", "discovery_observed", "repository_absent")):
            errors.append("result.runtime_flags_invalid")
    artifact = payload.get("artifact")
    if not _exact(artifact, {"zip_sha256", "member_manifest_sha256"}) or not all(
        _digest(artifact.get(key)) for key in ("zip_sha256", "member_manifest_sha256")
    ):
        errors.append("result.artifact_invalid")
    scenarios = payload.get("scenarios")
    seen: set[str] = set()
    scenario_keys = {"id", "state", "result", "evidence_sha256", "limitations"}
    if not isinstance(scenarios, list) or len(scenarios) != 7:
        errors.append("result.scenarios_invalid")
    else:
        for item in scenarios:
            if not _exact(item, scenario_keys):
                errors.append("result.scenario_invalid")
                continue
            assert isinstance(item, dict)
            identifier = item.get("id")
            if identifier not in {f"T{index}" for index in range(1, 8)} or identifier in seen:
                errors.append("result.scenario_id_invalid")
            elif isinstance(identifier, str):
                seen.add(identifier)
            if item.get("state") not in _STATES or item.get("result") not in _RESULTS:
                errors.append(f"result.scenario_state_invalid:{identifier}")
            evidence = item.get("evidence_sha256")
            if evidence is not None and not _digest(evidence):
                errors.append(f"result.scenario_evidence_invalid:{identifier}")
            limitations = item.get("limitations")
            if not isinstance(limitations, list) or any(not isinstance(value, str) for value in limitations) or len(limitations) != len(set(limitations)):
                errors.append(f"result.scenario_limitations_invalid:{identifier}")
        if seen != {f"T{index}" for index in range(1, 8)}:
            errors.append("result.scenarios_incomplete")
    tools = payload.get("tools")
    tool_keys = {"tool_id", "implementation_kind", "state", "executed", "network_contacted", "contract_sha256", "skill_bindings"}
    tool_ids: set[str] = set()
    if not isinstance(tools, list):
        errors.append("result.tools_invalid")
    else:
        for tool in tools:
            if not _exact(tool, tool_keys):
                errors.append("result.tool_invalid")
                continue
            assert isinstance(tool, dict)
            tool_id = tool.get("tool_id")
            if not isinstance(tool_id, str) or not tool_id or tool_id in tool_ids:
                errors.append("result.tool_id_invalid")
            else:
                tool_ids.add(tool_id)
            if tool.get("implementation_kind") not in _KINDS or tool.get("state") not in _STATES or not _digest(tool.get("contract_sha256")):
                errors.append(f"result.tool_contract_invalid:{tool_id}")
            if type(tool.get("executed")) is not bool or type(tool.get("network_contacted")) is not bool:
                errors.append(f"result.tool_flags_invalid:{tool_id}")
            bindings = tool.get("skill_bindings")
            if not isinstance(bindings, list) or not bindings or any(not isinstance(value, str) or not value for value in bindings) or len(bindings) != len(set(bindings)):
                errors.append(f"result.tool_bindings_invalid:{tool_id}")
    if payload.get("overall_state") not in _STATES:
        errors.append("result.overall_state_invalid")
    return tuple(sorted(set(errors)))


def _argv(value: object, *, nullable: bool = False) -> bool:
    if nullable and value is None:
        return True
    return isinstance(value, list) and all(isinstance(item, str) and item for item in value)


def _validate_runtime_result_v2(payload: object) -> tuple[str, ...]:
    errors: list[str] = []
    root_keys = {
        "schema", "runtime", "artifact", "scenarios", "tools",
        "evidence_states", "overall_state",
    }
    if not _exact(payload, root_keys):
        return ("result.invalid_object",)
    assert isinstance(payload, dict)
    runtime = payload.get("runtime")
    runtime_keys = {
        "name", "version", "os", "clean_workspace", "upload_observed",
        "discovery_observed", "repository_absent", "envelope_profile",
    }
    if not _exact(runtime, runtime_keys):
        errors.append("result.runtime_invalid")
    else:
        assert isinstance(runtime, dict)
        if runtime.get("name") not in _RUNTIMES or not isinstance(runtime.get("version"), str) or not runtime["version"] or not isinstance(runtime.get("os"), str) or not runtime["os"]:
            errors.append("result.runtime_identity_invalid")
        if any(type(runtime.get(key)) is not bool for key in ("clean_workspace", "upload_observed", "discovery_observed", "repository_absent")):
            errors.append("result.runtime_flags_invalid")
        if runtime.get("envelope_profile") != "PORTABLE_SINGLE_DIRECTORY":
            errors.append("result.runtime_envelope_invalid")
    artifact = payload.get("artifact")
    if not _exact(artifact, {"zip_sha256", "member_manifest_sha256"}) or not all(
        _digest(artifact.get(key)) for key in ("zip_sha256", "member_manifest_sha256")
    ):
        errors.append("result.artifact_invalid")
    scenarios = payload.get("scenarios")
    seen: set[str] = set()
    evidence_backed_runtime_scenarios = 0
    scenario_keys = {"id", "state", "result", "evidence_sha256", "limitations"}
    if not isinstance(scenarios, list) or len(scenarios) != 7:
        errors.append("result.scenarios_invalid")
    else:
        for item in scenarios:
            if not _exact(item, scenario_keys):
                errors.append("result.scenario_invalid")
                continue
            assert isinstance(item, dict)
            identifier = item.get("id")
            if identifier not in {f"T{index}" for index in range(1, 8)} or identifier in seen:
                errors.append("result.scenario_id_invalid")
            elif isinstance(identifier, str):
                seen.add(identifier)
            if item.get("state") not in _STATES or item.get("result") not in _RESULTS:
                errors.append(f"result.scenario_state_invalid:{identifier}")
            evidence = item.get("evidence_sha256")
            if evidence is not None and not _digest(evidence):
                errors.append(f"result.scenario_evidence_invalid:{identifier}")
            if item.get("state") == "RUNTIME VERIFIED" and _digest(evidence):
                evidence_backed_runtime_scenarios += 1
            limitations = item.get("limitations")
            if not isinstance(limitations, list) or any(not isinstance(value, str) for value in limitations) or len(limitations) != len(set(limitations)):
                errors.append(f"result.scenario_limitations_invalid:{identifier}")
        if seen != {f"T{index}" for index in range(1, 8)}:
            errors.append("result.scenarios_incomplete")
    tools = payload.get("tools")
    tool_keys = {
        "tool_id", "implementation_kind", "state", "executed", "network_contacted",
        "contract_sha256", "skill_bindings", "declared_argv", "observed_argv", "adapter",
    }
    tool_ids: set[str] = set()
    runtime_verified_tool = False
    if not isinstance(tools, list):
        errors.append("result.tools_invalid")
    else:
        for tool in tools:
            if not _exact(tool, tool_keys):
                errors.append("result.tool_invalid")
                continue
            assert isinstance(tool, dict)
            tool_id = tool.get("tool_id")
            if not isinstance(tool_id, str) or not tool_id or tool_id in tool_ids:
                errors.append("result.tool_id_invalid")
            else:
                tool_ids.add(tool_id)
            if tool.get("implementation_kind") not in _KINDS or tool.get("state") not in _STATES or not _digest(tool.get("contract_sha256")):
                errors.append(f"result.tool_contract_invalid:{tool_id}")
            if type(tool.get("executed")) is not bool or type(tool.get("network_contacted")) is not bool:
                errors.append(f"result.tool_flags_invalid:{tool_id}")
            bindings = tool.get("skill_bindings")
            if not isinstance(bindings, list) or not bindings or any(not isinstance(value, str) or not value for value in bindings) or len(bindings) != len(set(bindings)):
                errors.append(f"result.tool_bindings_invalid:{tool_id}")
            if not _argv(tool.get("declared_argv")) or not _argv(tool.get("observed_argv"), nullable=True):
                errors.append(f"result.tool_command_invalid:{tool_id}")
            adapter = tool.get("adapter")
            if adapter not in {None, "CURRENT_PYTHON"}:
                errors.append(f"result.tool_adapter_invalid:{tool_id}")
            if tool.get("executed") is True and tool.get("observed_argv") is None:
                errors.append(f"result.tool_observed_command_required:{tool_id}")
            if tool.get("state") == "RUNTIME VERIFIED" and tool.get("executed") is True:
                runtime_verified_tool = True
    layer_keys = {
        "structural_validation", "installation", "tool_execution",
        "reference_consultation", "conversation",
    }
    layers = payload.get("evidence_states")
    if not _exact(layers, layer_keys):
        errors.append("result.evidence_states_invalid")
    else:
        assert isinstance(layers, dict)
        for layer, state in layers.items():
            if state not in _STATES:
                errors.append(f"result.evidence_state_invalid:{layer}")
        if layers.get("installation") == "RUNTIME VERIFIED" and (
            not isinstance(runtime, dict)
            or runtime.get("upload_observed") is not True
            or runtime.get("discovery_observed") is not True
        ):
            errors.append("result.installation_evidence_invalid")
        if layers.get("tool_execution") == "RUNTIME VERIFIED" and not runtime_verified_tool:
            errors.append("result.tool_execution_evidence_invalid")
        for layer in ("reference_consultation", "conversation"):
            if layers.get(layer) == "RUNTIME VERIFIED" and evidence_backed_runtime_scenarios == 0:
                errors.append(f"result.layer_evidence_required:{layer}")
    if payload.get("overall_state") not in _STATES:
        errors.append("result.overall_state_invalid")
    return tuple(sorted(set(errors)))


def _validate_runtime_result_v3(payload: object) -> tuple[str, ...]:
    """Validate the exact installed-artifact Skill-to-result evidence shape."""
    if not _exact(payload, {"schema", "runtime", "artifact", "scenarios", "tools", "evidence_states", "overall_state"}):
        return ("result.invalid_object",)
    assert isinstance(payload, dict)
    errors: list[str] = []
    if payload["schema"] != "plugin-builder-runtime-result-v3":
        errors.append("result.schema_invalid")
    if _contains_private_value(payload):
        errors.append("result.v3.private_value_forbidden")
    runtime = payload["runtime"]
    runtime_keys = {
        "name", "version", "os", "installation_channel", "clean_workspace", "upload_observed",
        "discovery_observed", "repository_absent", "envelope_profile",
    }
    if not _exact(runtime, runtime_keys):
        errors.append("result.runtime_invalid")
        runtime = {}
    if runtime.get("name") not in _RUNTIMES or any(not isinstance(runtime.get(key), str) or not runtime[key] for key in ("version", "os", "installation_channel")):
        errors.append("result.runtime_identity_invalid")
    if any(type(runtime.get(key)) is not bool for key in ("clean_workspace", "upload_observed", "discovery_observed", "repository_absent")):
        errors.append("result.runtime_flags_invalid")
    if runtime.get("envelope_profile") != "PORTABLE_SINGLE_DIRECTORY":
        errors.append("result.runtime_envelope_invalid")
    artifact = payload["artifact"]
    if not _exact(artifact, {"plugin_id", "version", "zip_sha256", "member_manifest_sha256"}):
        errors.append("result.artifact_invalid")
        artifact = {}
    if any(not isinstance(artifact.get(key), str) or not artifact[key] or artifact[key].startswith("REPLACE_") for key in ("plugin_id", "version")) or any(not _digest(artifact.get(key)) or artifact[key] == "0" * 64 for key in ("zip_sha256", "member_manifest_sha256")):
        errors.append("result.artifact_identity_invalid")
    scenarios = payload["scenarios"]
    scenario_ids: set[str] = set()
    if not isinstance(scenarios, list) or len(scenarios) != 8:
        errors.append("result.scenarios_invalid")
        scenarios = []
    for scenario in scenarios:
        if not _exact(scenario, {"id", "state", "result", "evidence_sha256", "limitations"}):
            errors.append("result.scenario_invalid")
            continue
        identifier = scenario["id"]
        if identifier not in {f"T{i}" for i in range(1, 9)} or identifier in scenario_ids:
            errors.append("result.scenario_id_invalid")
        else:
            scenario_ids.add(identifier)
        if scenario["state"] not in _STATES or scenario["result"] not in _RESULTS:
            errors.append(f"result.scenario_state_invalid:{identifier}")
        if scenario["evidence_sha256"] is not None and not _digest(scenario["evidence_sha256"]):
            errors.append(f"result.scenario_evidence_invalid:{identifier}")
        if scenario["state"] == "RUNTIME VERIFIED" and (scenario["result"] != "PASS" or not _digest(scenario["evidence_sha256"])):
            errors.append(f"result.scenario_runtime_claim_invalid:{identifier}")
        if not isinstance(scenario["limitations"], list) or any(not isinstance(item, str) for item in scenario["limitations"]):
            errors.append(f"result.scenario_limitations_invalid:{identifier}")
    if scenario_ids != {f"T{i}" for i in range(1, 9)}:
        errors.append("result.scenarios_incomplete")
    tools = payload["tools"]
    seen_tools: set[str] = set()
    seen_realizations: set[tuple[str, str, str, str]] = set()
    runtime_verified_realization = False
    if not isinstance(tools, list):
        errors.append("result.tools_invalid")
        tools = []
    layer_names = {
        "structural_validation", "installation", "skill_invocation", "capability_discovery",
        "operation_execution", "result_delivery", "skill_behavior",
    }
    realization_keys = {
        "target_runtime", "installation_channel", "skill_id", "capability_id", "operation_id",
        "adapter_id", "exposed_capability", "input_sha256", "output_sha256", "executed",
        "network_contacted", "permissions_observed", "layers", "state", "result", "limitations",
    }
    for tool in tools:
        if not _exact(tool, {"tool_id", "implementation_kind", "contract_sha256", "skill_bindings", "operation_execution", "realizations"}):
            errors.append("result.tool_invalid")
            continue
        tool_id = tool["tool_id"]
        if not isinstance(tool_id, str) or not tool_id or tool_id in seen_tools:
            errors.append("result.tool_id_invalid")
            continue
        seen_tools.add(tool_id)
        if tool["implementation_kind"] not in _KINDS or not _digest(tool["contract_sha256"]):
            errors.append(f"result.tool_contract_invalid:{tool_id}")
        bindings = tool["skill_bindings"]
        if not isinstance(bindings, list) or not bindings or any(not isinstance(item, str) or not item for item in bindings) or len(bindings) != len(set(bindings)):
            errors.append(f"result.tool_bindings_invalid:{tool_id}")
            bindings = []
        operation = tool["operation_execution"]
        if not _exact(operation, {"operation_id", "environment", "state", "evidence_sha256"}):
            errors.append(f"result.v3.operation_invalid:{tool_id}")
            operation = {}
        if not isinstance(operation.get("operation_id"), str) or not operation["operation_id"] or operation.get("state") not in _STATES:
            errors.append(f"result.v3.operation_state_invalid:{tool_id}")
        if operation.get("evidence_sha256") is not None and not _digest(operation["evidence_sha256"]):
            errors.append(f"result.v3.operation_digest_invalid:{tool_id}")
        if operation.get("state") == "RUNTIME VERIFIED" and not _digest(operation.get("evidence_sha256")):
            errors.append(f"result.v3.operation_digest_required:{tool_id}")
        if operation.get("environment") not in {"INSTALLED_RUNTIME", "BUILD_HOST_LOCAL_MCP", "BUILD_HOST_DIRECT_ARGV", "NOT EXECUTED"}:
            errors.append(f"result.v3.operation_environment_invalid:{tool_id}")
        if operation.get("state") == "RUNTIME VERIFIED" and operation.get("environment") != "INSTALLED_RUNTIME":
            errors.append("result.v3.local_operation_not_installed")
        realizations = tool["realizations"]
        if not isinstance(realizations, list):
            errors.append(f"result.v3.realizations_invalid:{tool_id}")
            continue
        for realization in realizations:
            if not _exact(realization, realization_keys):
                errors.append("result.v3.realization_invalid")
                continue
            identity = (tool_id, realization["target_runtime"], realization["installation_channel"], realization["skill_id"])
            if identity in seen_realizations:
                errors.append("result.v3.realization_duplicate")
            seen_realizations.add(identity)
            if realization["target_runtime"] != runtime.get("name") or realization["installation_channel"] != runtime.get("installation_channel"):
                errors.append("result.v3.cross_runtime_realization")
            if realization["skill_id"] not in bindings or realization["operation_id"] != operation.get("operation_id"):
                errors.append("result.v3.realization_binding_invalid")
            if any(not isinstance(realization[key], str) or not realization[key] for key in ("capability_id", "adapter_id", "exposed_capability")):
                errors.append("result.v3.realization_identity_invalid")
            adapter = next((item for item in adapter_registry() if item.adapter_id == realization["adapter_id"]), None)
            if realization["state"] == "RUNTIME VERIFIED" and (
                adapter is None or realization["target_runtime"] not in adapter.runtime_targets
                or realization["installation_channel"] not in adapter.installation_channels
            ):
                errors.append("result.v3.adapter_unsupported")
            if any(value is not None and not _digest(value) for value in (realization["input_sha256"], realization["output_sha256"])):
                errors.append("result.v3.payload_digest_invalid")
            if type(realization["executed"]) is not bool or type(realization["network_contacted"]) is not bool:
                errors.append("result.v3.execution_flags_invalid")
            permissions = realization["permissions_observed"]
            if not isinstance(permissions, list) or any(not isinstance(item, str) or not item or re.search(r"(?i)(secret|token|password|credential)\s*[:=]", item) for item in permissions):
                errors.append("result.v3.permissions_invalid")
            if realization["state"] not in _STATES or realization["result"] not in _RESULTS:
                errors.append("result.v3.state_invalid")
            if not isinstance(realization["limitations"], list) or any(not isinstance(item, str) for item in realization["limitations"]):
                errors.append("result.v3.limitations_invalid")
            layers = realization["layers"]
            if not _exact(layers, layer_names):
                errors.append("result.v3.layers_invalid")
                continue
            for name, layer in layers.items():
                if not _exact(layer, {"state", "evidence_sha256"}) or layer["state"] not in _STATES:
                    errors.append(f"result.v3.layer_invalid:{name}")
                    continue
                if layer["evidence_sha256"] is not None and not _digest(layer["evidence_sha256"]):
                    errors.append(f"result.v3.layer_digest_invalid:{name}")
                if layer["state"] == "RUNTIME VERIFIED" and not _digest(layer["evidence_sha256"]):
                    errors.append(f"result.v3.layer_digest_required:{name}")
            if realization["state"] == "RUNTIME VERIFIED":
                runtime_verified_realization = True
                if (
                    realization["result"] != "PASS" or realization["executed"] is not True
                    or not _digest(realization["input_sha256"]) or not _digest(realization["output_sha256"])
                    or any(layers[name].get("state") != "RUNTIME VERIFIED" for name in layer_names)
                    or operation.get("state") != "RUNTIME VERIFIED"
                    or runtime.get("upload_observed") is not True or runtime.get("discovery_observed") is not True
                ):
                    errors.append("result.v3.realization_claim_incomplete")
    evidence_states = payload["evidence_states"]
    if not _exact(evidence_states, {"structural_validation", "installation", "tool_execution", "reference_consultation", "conversation"}) or any(value not in _STATES for value in evidence_states.values()):
        errors.append("result.evidence_states_invalid")
    elif evidence_states["installation"] == "RUNTIME VERIFIED" and (
        runtime.get("upload_observed") is not True or runtime.get("discovery_observed") is not True
    ):
        errors.append("result.installation_evidence_invalid")
    elif evidence_states["tool_execution"] == "RUNTIME VERIFIED" and not runtime_verified_realization:
        errors.append("result.tool_execution_evidence_invalid")
    if payload["overall_state"] not in _STATES:
        errors.append("result.overall_state_invalid")
    elif payload["overall_state"] == "RUNTIME VERIFIED" and (
        not runtime_verified_realization or any(
            scenario.get("state") not in {"RUNTIME VERIFIED", "NOT APPLICABLE"}
            for scenario in scenarios if isinstance(scenario, dict)
        )
    ):
        errors.append("result.v3.overall_claim_invalid")
    t8 = next((item for item in scenarios if isinstance(item, dict) and item.get("id") == "T8"), None)
    if isinstance(t8, dict) and t8.get("state") == "RUNTIME VERIFIED" and not runtime_verified_realization:
        errors.append("result.v3.t8_realization_required")
    return tuple(sorted(set(errors)))


def validate_runtime_result_v3(payload: object) -> tuple[str, ...]:
    try:
        return _validate_runtime_result_v3(payload)
    except (TypeError, KeyError, ValueError, AttributeError):
        return ("result.v3.invalid_type",)


def validate_runtime_result(payload: object) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return ("result.invalid_object",)
    schema = payload.get("schema")
    if schema == "plugin-builder-runtime-result-v1":
        return _validate_runtime_result_v1(payload)
    if schema == "plugin-builder-runtime-result-v2":
        return _validate_runtime_result_v2(payload)
    if schema == "plugin-builder-runtime-result-v3":
        return validate_runtime_result_v3(payload)
    return ("result.schema_invalid",)


def build_runtime_evidence_bundle(result_path: Path, evidence_root: Path, destination: Path) -> EvidenceBundleOutcome:
    result_file = Path(result_path)
    try:
        result_bytes = result_file.read_bytes()
        payload = json.loads(result_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return EvidenceBundleOutcome("FAIL", ("result.unreadable",))
    validation = validate_runtime_result(payload)
    if validation:
        return EvidenceBundleOutcome("FAIL", validation)
    assert isinstance(payload, dict)
    required = {
        item["evidence_sha256"] for item in payload["scenarios"]
        if isinstance(item, dict) and item.get("evidence_sha256") is not None
    }
    if payload["schema"] == "plugin-builder-runtime-result-v3":
        for tool in payload["tools"]:
            operation_digest = tool["operation_execution"]["evidence_sha256"]
            if operation_digest is not None:
                required.add(operation_digest)
            for realization in tool["realizations"]:
                required.update(
                    layer["evidence_sha256"] for layer in realization["layers"].values()
                    if layer["evidence_sha256"] is not None
                )
    root = Path(evidence_root)
    if not root.is_dir() or root.is_symlink():
        return EvidenceBundleOutcome("FAIL", ("evidence.root_invalid",))
    indexed: dict[str, list[Path]] = {}
    extra = False
    for path in sorted(root.iterdir(), key=lambda item: item.name):
        if not path.is_file() or path.is_symlink():
            extra = True
            continue
        if _SHA256.fullmatch(path.stem):
            indexed.setdefault(path.stem, []).append(path)
        else:
            extra = True
    errors: list[str] = []
    for digest in sorted(required):
        matches = indexed.get(digest, [])
        if not matches:
            errors.append(f"evidence.missing:{digest}")
        elif len(matches) != 1:
            errors.append(f"evidence.duplicate:{digest}")
        elif sha256(matches[0].read_bytes()).hexdigest() != digest:
            errors.append(f"evidence.digest_mismatch:{digest}")
    if extra or set(indexed) - required:
        errors.append("evidence.unindexed")
    if errors:
        return EvidenceBundleOutcome("FAIL", tuple(sorted(set(errors))))
    result_digest = sha256(result_bytes).hexdigest()
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(dir=destination_path.parent, prefix=f".{destination_path.name}.evidence-") as name:
            stage = Path(name) / "bundle"
            (stage / "evidence").mkdir(parents=True)
            (stage / "results").mkdir()
            evidence_records = []
            for digest in sorted(required):
                source = indexed[digest][0]
                relative = f"evidence/{source.name}"
                staged = stage / relative
                shutil.copyfile(source, staged)
                staged_bytes = staged.read_bytes()
                if sha256(staged_bytes).hexdigest() != digest:
                    return EvidenceBundleOutcome("FAIL", (f"evidence.digest_mismatch:{digest}",))
                evidence_records.append({"path": relative, "sha256": digest, "size": len(staged_bytes)})
            result_relative = f"results/{result_digest}.json"
            (stage / result_relative).write_bytes(result_bytes)
            index = {
                "schema": "plugin-builder-runtime-evidence-index-v1",
                "result": {"path": result_relative, "sha256": result_digest, "size": len(result_bytes)},
                "evidence": evidence_records,
            }
            index_bytes = canonical_bytes(index)
            (stage / "evidence-index.json").write_bytes(index_bytes)
            archive_digest = plugin_authoring.write_deterministic_zip(stage, destination_path)
    except (OSError, plugin_authoring.PluginAuthoringError):
        return EvidenceBundleOutcome("FAIL", ("evidence.bundle_write_failed",))
    return EvidenceBundleOutcome("PASS", (), archive_digest, result_digest, sha256(index_bytes).hexdigest())
