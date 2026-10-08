"""Safe, direct-argv verification for approved application-tool contracts."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from typing import Any

from .implementation_plan import canonical_bytes
from .runtime_commands import resolve_direct_argv
from .mcp_local_verification import verify_local_mcp_realization


def _digest(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def _permission_records(tool: dict[str, Any]) -> tuple[list[Any], frozenset[str]]:
    """Return deterministically ordered permissions and their declared IDs.

    Application-tool v1 stores permissions as strings. Version 2 stores exact
    per-runtime permission records. Build-host verification preserves either
    representation in evidence, but authorization decisions use only the
    declared identifiers.
    """
    permissions = tool.get("permissions", [])
    if not isinstance(permissions, list):
        return [], frozenset()
    ordered = sorted(permissions, key=canonical_bytes)
    identifiers = frozenset(
        item if isinstance(item, str) else str(item.get("id", ""))
        for item in permissions
        if isinstance(item, (str, dict))
    )
    return ordered, identifiers


def execute_direct(argv: list[str], candidate: Path, timeout: int, stdin_payload: bytes | None = None) -> dict[str, Any]:
    recorded = list(argv)
    resolution = resolve_direct_argv(argv, candidate)
    common = {
        "argv": recorded,
        "declared_argv": recorded,
        "observed_argv": list(resolution.observed_argv) if resolution.observed_argv is not None else None,
        "adapter": resolution.adapter,
    }
    if resolution.observed_argv is None:
        return {
            **common,
            "diagnostics": [resolution.diagnostic or "executable_unavailable"],
            "executed": False,
            "state": "NOT VERIFIED",
            "stdout_sha256": None,
            "stderr_sha256": None,
        }
    command = list(resolution.observed_argv)
    environment = {
        key: value for key, value in os.environ.items()
        if key.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}
    }
    environment.update({"PATH": "", "PYTHONIOENCODING": "utf-8", "PYTHONNOUSERSITE": "1"})
    try:
        completed = subprocess.run(
            command, cwd=candidate, env=environment, shell=False,
            input=stdin_payload, stdin=subprocess.DEVNULL if stdin_payload is None else None,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=timeout, check=False,
        )
    except FileNotFoundError:
        return {
            **common, "diagnostics": ["executable_unavailable"], "executed": False,
            "state": "NOT VERIFIED", "stdout_sha256": None, "stderr_sha256": None,
        }
    except subprocess.TimeoutExpired as error:
        return {
            **common, "diagnostics": ["execution_timeout"], "executed": True,
            "state": "FAIL", "stdout_sha256": _digest(error.stdout or b""),
            "stderr_sha256": _digest(error.stderr or b""),
        }
    state = "PASS" if completed.returncode == 0 else "FAIL"
    diagnostics = [] if state == "PASS" else [f"process_exit:{completed.returncode}"]
    return {
        **common, "diagnostics": diagnostics, "executed": True,
        "state": state, "stdout_sha256": _digest(completed.stdout),
        "stderr_sha256": _digest(completed.stderr), "_stdout": completed.stdout,
    }


def verify_application_tool(
    tool: dict[str, Any],
    candidate: Path,
    *,
    runtime_capabilities: frozenset[str] = frozenset(),
    allow_network: bool = False,
    allow_loopback: bool = False,
) -> dict[str, Any]:
    kind = str(tool.get("implementation_kind", ""))
    permissions, permission_ids = _permission_records(tool)
    base: dict[str, Any] = {
        "tool_id": str(tool.get("id", "")), "implementation_kind": kind,
        "required": tool.get("required") is True,
        "requirement_ids": sorted(tool.get("requirement_ids", [])),
        "skill_bindings": sorted(tool.get("skill_bindings", [])),
        "permissions": permissions,
        "fallback": tool.get("fallback"), "executed": False,
        "argv": list((tool.get("verification") or {}).get("argv", [])),
        "declared_argv": list((tool.get("verification") or {}).get("argv", [])),
        "observed_argv": None,
        "adapter": None,
        "fixture_sha256": _digest(canonical_bytes(tool.get("fixtures"))),
        "contract_sha256": _digest(canonical_bytes(tool)),
        "stdout_sha256": None, "stderr_sha256": None,
    }
    if kind == "RUNTIME_NATIVE":
        capability = (tool.get("runtime_capability") or {}).get("name")
        if capability not in runtime_capabilities:
            return {**base, "state": "NOT VERIFIED", "diagnostics": ["runtime_capability_unavailable"]}
        return {**base, "state": "NOT VERIFIED", "diagnostics": ["runtime_execution_evidence_required"]}
    if kind == "MCP_ADAPTER":
        if allow_loopback and tool.get("schema") == "plugin-builder-application-tool-v2":
            local = verify_local_mcp_realization(tool, Path(candidate), allow_loopback=True)
            return {**base, **local}
        return {**base, "state": "NOT VERIFIED", "diagnostics": ["mcp_runtime_evidence_required"]}
    if kind not in {"BUNDLED_LOCAL", "FRAMEWORK_ADAPTER"}:
        return {**base, "state": "NOT VERIFIED", "diagnostics": ["tool_implementation_unavailable"]}
    authentication = (tool.get("configuration") or {}).get("authentication")
    verification = tool.get("verification") or {}
    contract_version = str(tool.get("schema", ""))
    verification_uses_network = (
        verification.get("network") is True
        if contract_version == "plugin-builder-application-tool-v2"
        else "network" in permission_ids
    )
    if verification_uses_network and not allow_network or authentication != "NOT_REQUIRED":
        return {**base, "state": "NOT VERIFIED", "diagnostics": ["runtime_authorization_required"]}
    argv = verification.get("argv")
    execution = tool.get("execution") or {}
    if not isinstance(argv, list) or not argv:
        return {**base, "state": "NOT VERIFIED", "diagnostics": ["verification_argv_missing"]}
    fixtures = tool.get("fixtures") or {}
    result = execute_direct(
        argv, Path(candidate), int(execution.get("timeout_seconds", 30)),
        canonical_bytes(fixtures.get("input")),
    )
    stdout = result.pop("_stdout", b"")
    if result["state"] == "PASS":
        try:
            actual = json.loads(stdout.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            result["state"] = "FAIL"
            result["diagnostics"] = ["fixture_output_invalid_json"]
        else:
            if actual != fixtures.get("output"):
                result["state"] = "FAIL"
                result["diagnostics"] = ["fixture_output_mismatch"]
    return {**base, **result}
