"""Opt-in loopback verification of a W1-declared MCP operation."""

from __future__ import annotations

from hashlib import sha256
import http.client
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
from typing import Any

from .implementation_plan import canonical_bytes
from .runtime_commands import resolve_direct_argv


def _digest(value: object) -> str:
    return sha256(canonical_bytes(value)).hexdigest()


def _invalid_input(tool: dict[str, Any], valid: dict[str, Any]) -> dict[str, Any] | None:
    """Derive a negative call only when the declared schema proves it invalid."""
    schema = tool.get("input_schema")
    if not isinstance(schema, dict):
        return None
    required = schema.get("required")
    if isinstance(required, list):
        for name in required:
            if isinstance(name, str) and name in valid:
                invalid = dict(valid)
                invalid.pop(name)
                return invalid
    properties = schema.get("properties")
    if isinstance(properties, dict):
        for name, definition in properties.items():
            if name not in valid or not isinstance(definition, dict):
                continue
            kind = definition.get("type")
            replacement = 7 if kind == "string" else "not-a-number" if kind in {"integer", "number"} else None
            if replacement is not None:
                invalid = dict(valid)
                invalid[name] = replacement
                return invalid
    return None


def _request(port: int, method: str, params: dict[str, Any], identifier: int, timeout: float) -> dict[str, Any]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        body = canonical_bytes({"jsonrpc": "2.0", "id": identifier, "method": method, "params": params})
        connection.request("POST", "/mcp", body, {"content-type": "application/json", "accept": "application/json, text/event-stream"})
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError(f"http_status_{response.status}")
        if response.getheader("content-type", "").split(";", 1)[0] != "application/json":
            raise ValueError("content_type_invalid")
        length = response.getheader("content-length")
        if length is not None:
            if not length.isdigit() or int(length) > 1024 * 1024:
                raise ValueError("content_length_invalid")
            body = response.read(int(length))
        elif response.chunked:
            body = response.read(1024 * 1024 + 1)
            if len(body) > 1024 * 1024:
                raise ValueError("response_too_large")
        else:
            raise ValueError("response_framing_invalid")
        payload = json.loads(body.decode("utf-8"))
        if not isinstance(payload, dict) or payload.get("jsonrpc") != "2.0" or payload.get("id") != identifier:
            raise ValueError("jsonrpc_envelope_invalid")
        return payload
    finally:
        connection.close()


def _base(tool: dict[str, Any]) -> dict[str, Any]:
    return {
        "state": "NOT VERIFIED", "environment": "BUILD_HOST_LOCAL_MCP",
        "executed": False, "network_contacted": False,
        "process_cleanup": "NOT APPLICABLE", "diagnostics": [],
        "input_sha256": None, "output_sha256": None, "transcript_sha256": None,
        "operation_execution": {"state": "NOT VERIFIED", "evidence_sha256": None},
        "realizations": [{
            "target_runtime": item.get("target_runtime"), "state": "NOT VERIFIED",
            "layers": {
                "skill_invocation": "NOT VERIFIED", "capability_discovery": "NOT VERIFIED",
                "operation_execution": "NOT VERIFIED", "result_delivery": "NOT VERIFIED",
                "skill_behavior": "NOT VERIFIED",
            },
        } for item in tool.get("realizations", []) if isinstance(item, dict)],
    }


def _preflight(tool: dict[str, Any], candidate: Path, allow_loopback: bool) -> tuple[list[str] | None, list[str]]:
    if not allow_loopback:
        return None, ["mcp_local.loopback_not_authorized"]
    verification = tool.get("verification")
    argv = verification.get("argv") if isinstance(verification, dict) else None
    if not isinstance(argv, list) or len(argv) < 6 or verification.get("kind") != "MCP_CONTRACT":
        return None, ["mcp_local.argv_undeclared"]
    if argv[2:6] != ["--host", "127.0.0.1", "--port", "{port}"]:
        return None, ["mcp_local.external_host_forbidden"]
    if any(arg.startswith("--") and arg not in {"--host", "--port", "--mode"} for arg in argv[2:]):
        return None, ["mcp_local.argv_undeclared"]
    server_file = argv[1]
    if server_file not in tool.get("files", []):
        return None, [f"mcp_local.server_file_undeclared:{server_file}"]
    server_path = (candidate / server_file).resolve()
    if not server_path.is_file() or not server_path.is_relative_to(candidate.resolve()):
        return None, ["mcp_local.server_file_invalid"]
    dependencies = tool.get("dependencies")
    if not isinstance(dependencies, list) or not any(
        isinstance(item, dict) and item.get("type") == "EXECUTABLE" and item.get("id") == "python-runtime"
        for item in dependencies
    ):
        return None, ["mcp_local.dependency_undeclared"]
    resolution = resolve_direct_argv([argv[0], *argv[1:5], "0", *argv[6:]], candidate)
    if resolution.observed_argv is None:
        return None, [f"mcp_local.{resolution.diagnostic}"]
    return list(resolution.observed_argv), []


def verify_local_mcp_realization(tool: dict[str, Any], candidate: Path, *, allow_loopback: bool = False) -> dict[str, Any]:
    """Exercise only the declared local operation; never claim installed use."""
    evidence = _base(tool)
    command, errors = _preflight(tool, Path(candidate), allow_loopback)
    if errors:
        evidence["diagnostics"] = errors
        return evidence
    assert command is not None
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    command[5] = str(port)
    environment = {
        key: value for key, value in os.environ.items()
        if key.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}
    }
    environment.update({"PATH": "", "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "PYTHONNOUSERSITE": "1"})
    process: subprocess.Popen[bytes] | None = None
    try:
        with tempfile.TemporaryDirectory() as scratch:
            environment["TEMP"] = scratch
            environment["TMP"] = scratch
            process = subprocess.Popen(
                command, cwd=Path(candidate), env=environment, shell=False,
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            deadline = time.monotonic() + 2.0
            initialized: dict[str, Any] | None = None
            last_connection_error = ""
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    evidence["diagnostics"] = ["mcp_local.startup_failed" if process.returncode else "mcp_local.premature_exit"]
                    evidence["state"] = "FAIL"
                    return evidence
                try:
                    initialized = _request(port, "initialize", {
                        "protocolVersion": "2025-06-18", "capabilities": {},
                        "clientInfo": {"name": "plugin-builder-local-test", "version": "1"},
                    }, 1, 0.25)
                    break
                except (ConnectionError, OSError, TimeoutError) as error:
                    last_connection_error = type(error).__name__
                    time.sleep(0.025)
                except (ValueError, UnicodeError, json.JSONDecodeError) as error:
                    evidence["diagnostics"] = ["mcp_local.response_invalid", str(error)]
                    evidence["state"] = "FAIL"
                    return evidence
            if initialized is None:
                evidence["diagnostics"] = ["mcp_local.request_timeout", last_connection_error]
                evidence["state"] = "FAIL"
                return evidence
            evidence["network_contacted"] = True
            if not isinstance(initialized.get("result"), dict) or "tools" not in initialized["result"].get("capabilities", {}):
                raise ValueError("response_invalid")
            listed = _request(port, "tools/list", {}, 2, 2.0)
            tools = (listed.get("result") or {}).get("tools")
            operation_id = tool.get("operation", {}).get("id")
            if not isinstance(tools, list) or operation_id not in [row.get("name") for row in tools if isinstance(row, dict)]:
                evidence["diagnostics"] = [f"mcp_local.tool_not_advertised:{operation_id}"]
                evidence["state"] = "FAIL"
                return evidence
            fixtures = tool.get("fixtures") or {}
            fixture_input = fixtures.get("input")
            fixture_output = fixtures.get("output")
            if not isinstance(fixture_input, dict) or not isinstance(fixture_output, dict):
                evidence["diagnostics"] = ["mcp_local.fixture_invalid"]
                evidence["state"] = "FAIL"
                return evidence
            negative_input = _invalid_input(tool, fixture_input)
            if negative_input is None:
                evidence["diagnostics"] = ["mcp_local.negative_fixture_unavailable"]
                return evidence
            invalid = _request(port, "tools/call", {"name": operation_id, "arguments": negative_input}, 3, 2.0)
            if (invalid.get("result") or {}).get("isError") is not True:
                raise ValueError("invalid_input_not_rejected")
            called = _request(port, "tools/call", {"name": operation_id, "arguments": fixture_input}, 4, 2.0)
            result = called.get("result")
            if not isinstance(result, dict) or result.get("isError") is not False or result.get("structuredContent") != fixture_output:
                raise ValueError("output_mismatch")
            evidence.update({
                "state": "PASS", "executed": True,
                "input_sha256": _digest(fixture_input), "output_sha256": _digest(fixture_output),
                "transcript_sha256": _digest([initialized, listed, invalid, called]),
            })
            evidence["operation_execution"] = {"state": "PASS", "evidence_sha256": evidence["transcript_sha256"]}
            for realization in evidence["realizations"]:
                realization["layers"]["operation_execution"] = "STATICALLY VERIFIED"
            return evidence
    except (TimeoutError, socket.timeout):
        evidence.update(state="FAIL", diagnostics=["mcp_local.request_timeout"])
    except (ValueError, UnicodeError, json.JSONDecodeError, http.client.HTTPException) as error:
        evidence.update(state="FAIL", diagnostics=["mcp_local.response_invalid", str(error)])
    except OSError:
        evidence.update(state="FAIL", diagnostics=["mcp_local.startup_failed"])
    finally:
        if process is not None:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
            evidence["process_cleanup"] = "PASS"
    return evidence


__all__ = ["verify_local_mcp_realization"]
