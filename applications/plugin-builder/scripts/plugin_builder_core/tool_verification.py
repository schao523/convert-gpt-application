"""Safe, direct-argv verification for approved application-tool contracts."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from .implementation_plan import canonical_bytes


def _digest(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def execute_direct(argv: list[str], candidate: Path, timeout: int, stdin_payload: bytes | None = None) -> dict[str, Any]:
    recorded = list(argv)
    command = list(argv)
    if command and command[0] in {"python", "python3"}:
        command[0] = sys.executable
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
            "argv": recorded, "diagnostics": ["executable_unavailable"], "executed": False,
            "state": "NOT VERIFIED", "stdout_sha256": None, "stderr_sha256": None,
        }
    except subprocess.TimeoutExpired as error:
        return {
            "argv": recorded, "diagnostics": ["execution_timeout"], "executed": True,
            "state": "FAIL", "stdout_sha256": _digest(error.stdout or b""),
            "stderr_sha256": _digest(error.stderr or b""),
        }
    state = "PASS" if completed.returncode == 0 else "FAIL"
    diagnostics = [] if state == "PASS" else [f"process_exit:{completed.returncode}"]
    return {
        "argv": recorded, "diagnostics": diagnostics, "executed": True,
        "state": state, "stdout_sha256": _digest(completed.stdout),
        "stderr_sha256": _digest(completed.stderr), "_stdout": completed.stdout,
    }


def verify_application_tool(
    tool: dict[str, Any],
    candidate: Path,
    *,
    runtime_capabilities: frozenset[str] = frozenset(),
    allow_network: bool = False,
) -> dict[str, Any]:
    kind = str(tool.get("implementation_kind", ""))
    base: dict[str, Any] = {
        "tool_id": str(tool.get("id", "")), "implementation_kind": kind,
        "required": tool.get("required") is True,
        "requirement_ids": sorted(tool.get("requirement_ids", [])),
        "skill_bindings": sorted(tool.get("skill_bindings", [])),
        "permissions": sorted(tool.get("permissions", [])),
        "fallback": tool.get("fallback"), "executed": False,
        "argv": list((tool.get("verification") or {}).get("argv", [])),
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
        return {**base, "state": "NOT VERIFIED", "diagnostics": ["mcp_runtime_evidence_required"]}
    if kind not in {"BUNDLED_LOCAL", "FRAMEWORK_ADAPTER"}:
        return {**base, "state": "NOT VERIFIED", "diagnostics": ["tool_implementation_unavailable"]}
    authentication = (tool.get("configuration") or {}).get("authentication")
    if "network" in tool.get("permissions", []) and not allow_network or authentication != "NOT_REQUIRED":
        return {**base, "state": "NOT VERIFIED", "diagnostics": ["runtime_authorization_required"]}
    verification = tool.get("verification") or {}
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
