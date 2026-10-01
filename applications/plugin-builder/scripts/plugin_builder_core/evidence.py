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


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_STATES = {"EXPECTED", "STATICALLY VERIFIED", "RUNTIME VERIFIED", "NOT VERIFIED", "NOT APPLICABLE"}
_RESULTS = {"PASS", "FAIL", "NOT VERIFIED", "NOT APPLICABLE"}
_RUNTIMES = {"Codex", "ChatGPT Work Local/Desktop"}
_KINDS = {"BUNDLED_LOCAL", "FRAMEWORK_ADAPTER", "RUNTIME_NATIVE", "MCP_ADAPTER"}


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


def validate_runtime_result(payload: object) -> tuple[str, ...]:
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
