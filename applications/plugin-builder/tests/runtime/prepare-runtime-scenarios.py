#!/usr/bin/env python3
"""Derive exact T3/T5/T6/T8 plans and the deterministic T4 baseline/plan."""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import zipfile


FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")


def write_plan(path: Path, value: dict) -> None:
    path.write_bytes(canonical(value))


def derive(base: dict, output: Path, baseline: Path | None = None) -> dict[str, str]:
    output.mkdir(parents=True, exist_ok=True)
    unresolved = deepcopy(base)
    tool = unresolved["tools"][0]
    tool.update({"implementation_kind": "UNRESOLVED", "files": [], "execution": None, "fixtures": None})
    write_plan(output / "t3-unresolved-plan.json", unresolved)

    failing = deepcopy(base)
    recipe = next(item for item in failing["files"] if item["path"] == "tools/normalize.py")
    recipe["inline_text"] = "raise SystemExit(23)\n"
    recipe["source_sha256"] = sha256(recipe["inline_text"].encode()).hexdigest()
    write_plan(output / "t5-failing-tool-plan.json", failing)

    limited = deepcopy(base)
    tool = limited["tools"][0]
    skill = next(item for item in limited["files"] if item["path"] == "skills/answering-structured-requests/SKILL.md")
    skill["inline_text"] += "\nThe optional runtime-exposed capability is `desktop-picker`; use it only when available.\n"
    skill["source_sha256"] = sha256(skill["inline_text"].encode("utf-8")).hexdigest()
    tool.update({
        "required": False, "implementation_kind": "RUNTIME_NATIVE", "files": [],
        "execution": None, "fixtures": None, "mcp": None,
        "runtime_capability": {"name": "desktop-picker", "runtimes": tool["runtime_targets"]},
        "dependencies": [{"id": "desktop-picker-runtime", "type": "RUNTIME_CAPABILITY", "provider": "RUNTIME_PROVIDED", "version": None, "sha256": None, "runtime_targets": tool["runtime_targets"], "setup_owner": "RUNTIME", "required": False, "absence_policy": "FALLBACK"}],
        "permissions": [{"id": "runtime:native", "target_runtime": target, "grant_source": "RUNTIME", "required": False, "purpose": "Use the runtime-provided desktop picker.", "verification": "Observe installed runtime capability discovery."} for target in tool["runtime_targets"]],
        "fallback": {"policy": "OMIT_OPTIONAL", "trigger_conditions": ["The runtime-native picker is unavailable."], "alternative_operation_id": None, "preserved_requirement_ids": [], "degraded_requirement_ids": ["RQ1"]},
        "verification": {"kind": "RUNTIME_CAPABILITY", "argv": [], "network": False},
        "realizations": [{"target_runtime": target, "mechanism": "RUNTIME_NATIVE", "adapter_id": "runtime-native", "adapter_version": "1", "exposed_capability": "desktop-picker", "operation_id": "normalize-input", "transport": "RUNTIME_API", "execution_location": "RUNTIME_HOST", "dependency_ids": ["desktop-picker-runtime"], "permission_ids": ["runtime:native"], "setup_requirements": [], "setup_owner": "RUNTIME", "feasibility_state": "NOT VERIFIED", "evidence_policy": "DEFERRED_ALLOWED"} for target in tool["runtime_targets"]],
    })
    tool["operation"]["protocol"] = "RUNTIME_API"
    limited["files"] = [item for item in limited["files"] if item["path"] != "tools/normalize.py"]
    limited["expected_members"].remove("tools/normalize.py")
    limited["expected_members"] = [item for item in limited["expected_members"] if item not in {"mcp.json", ".mcp.json"}]
    limited["checks"] = [item for item in limited["checks"] if item["id"] != "normalize-self-test"]
    requirement = next(item for item in limited["requirements"] if item["id"] == "RQ1")
    requirement["implementation_paths"].remove("tools/normalize.py")
    requirement["evidence_targets"].remove("normalize-self-test")
    write_plan(output / "t6-runtime-native-plan.json", limited)

    t8 = deepcopy(base)
    fixture = Path(__file__).with_name("mcp_server_fixture.py")
    if not fixture.is_file():
        fixture = Path(__file__).parent.parent / "fixtures" / "mcp_server_fixture.py"
    server = fixture.read_text(encoding="utf-8")
    recipe = next(item for item in t8["files"] if item["path"] == "tools/normalize.py")
    recipe.update({"path": "tools/server.py", "inline_text": server, "source_sha256": sha256(server.encode("utf-8")).hexdigest()})
    t8["expected_members"] = ["tools/server.py" if item == "tools/normalize.py" else item for item in t8["expected_members"]]
    requirement = next(item for item in t8["requirements"] if item["id"] == "RQ1")
    requirement["implementation_paths"] = ["tools/server.py" if item == "tools/normalize.py" else item for item in requirement["implementation_paths"]]
    requirement["evidence_targets"] = [item for item in requirement["evidence_targets"] if item != "normalize-self-test"]
    t8["checks"] = [item for item in t8["checks"] if item["id"] != "normalize-self-test"]
    mcp_tool = t8["tools"][0]
    mcp_tool.update({
        "implementation_kind": "MCP_ADAPTER", "files": ["tools/server.py"],
        "verification": {"kind": "MCP_CONTRACT", "argv": ["{python}", "tools/server.py", "--host", "127.0.0.1", "--port", "{port}"], "network": True},
        "execution": {"timeout_seconds": 2},
        "dependencies": [*mcp_tool["dependencies"], {"id": "python-runtime", "type": "EXECUTABLE", "provider": "RUNTIME_PROVIDED", "version": None, "sha256": None, "runtime_targets": mcp_tool["runtime_targets"], "setup_owner": "RUNTIME", "required": True, "absence_policy": "BLOCK"}],
    })
    write_plan(output / "t8-local-mcp-plan.json", t8)
    v3_template = json.loads(Path(__file__).with_name("runtime-result-v3-template.json").read_text(encoding="utf-8"))
    write_plan(output / "runtime-result-v3-template.json", v3_template)

    runtime_tools = []
    for item in base.get("tools", []):
        declared = list((item.get("verification") or {}).get("argv", []))
        runtime_tools.append({
            "tool_id": item["id"],
            "implementation_kind": item["implementation_kind"],
            "state": "NOT VERIFIED",
            "executed": False,
            "network_contacted": False,
            "contract_sha256": sha256(canonical(item)).hexdigest(),
            "skill_bindings": sorted(item.get("skill_bindings", [])),
            "declared_argv": declared,
            "observed_argv": None,
            "adapter": None,
        })
    runtime_template = {
        "schema": "plugin-builder-runtime-result-v2",
        "runtime": {
            "name": "Codex", "version": "UNRECORDED", "os": "UNRECORDED",
            "clean_workspace": True, "upload_observed": False,
            "discovery_observed": False, "repository_absent": True,
            "envelope_profile": "PORTABLE_SINGLE_DIRECTORY",
        },
        "artifact": {"zip_sha256": "0" * 64, "member_manifest_sha256": "0" * 64},
        "scenarios": [
            {
                "id": f"T{index}", "state": "NOT VERIFIED", "result": "NOT VERIFIED",
                "evidence_sha256": None, "limitations": ["replace template values with observed evidence"],
            }
            for index in range(1, 8)
        ],
        "tools": runtime_tools,
        "evidence_states": {
            "structural_validation": "STATICALLY VERIFIED",
            "installation": "NOT VERIFIED",
            "tool_execution": "NOT VERIFIED",
            "reference_consultation": "NOT VERIFIED",
            "conversation": "NOT VERIFIED",
        },
        "overall_state": "NOT VERIFIED",
    }
    write_plan(output / "runtime-result-v2-template.json", runtime_template)

    result = {
        "t3": "t3-unresolved-plan.json", "t5": "t5-failing-tool-plan.json",
        "t6": "t6-runtime-native-plan.json", "t8": "t8-local-mcp-plan.json",
        "runtime_result": "runtime-result-v2-template.json", "runtime_result_v3": "runtime-result-v3-template.json",
    }
    if baseline is not None:
        members: dict[str, bytes] = {}
        with zipfile.ZipFile(baseline) as source:
            files = [item for item in source.infolist() if not item.is_dir()]
            roots = {PurePosixPath(item.filename).parts[0] for item in files if PurePosixPath(item.filename).parts}
            if roots != {"sample-plugin"}:
                raise ValueError("baseline must contain exactly the sample-plugin directory")
            for item in files:
                members[item.filename] = source.read(item)
        members["sample-plugin/owner-notes.txt"] = b"owner bytes\x00preserved"
        update_baseline = output / "t4-update-baseline.zip"
        with zipfile.ZipFile(update_baseline, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name in sorted(members):
                info = zipfile.ZipInfo(name, FIXED_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, members[name])
        update = deepcopy(base)
        update["operation"] = "update"
        expected = {"/".join(PurePosixPath(name).parts[1:]) for name in members}
        expected.add("PLUGIN-BUILDER-CHANGES.json")
        update["expected_members"] = sorted(expected)
        write_plan(output / "t4-update-plan.json", update)
        result.update({"t4_baseline": update_baseline.name, "t4_plan": "t4-update-plan.json"})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-plan", type=Path, default=Path(__file__).with_name("create-plan.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    options = parser.parse_args()
    base = json.loads(options.base_plan.read_text(encoding="utf-8"))
    print(json.dumps({"status": "PASS", "files": derive(base, options.output, options.baseline)}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
