"""Deterministic projection of approved remote MCP realizations."""

from __future__ import annotations

import ipaddress
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any
from urllib.parse import urlsplit


MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_CREDENTIAL_KEYS = {
    "api-key", "api_key", "apikey", "authorization", "credential",
    "credentials", "password", "secret", "token",
}


def canonical_mcp_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")


def _safe_root_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and value == path.as_posix()


def _contains_credentials(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).casefold() in _CREDENTIAL_KEYS or _contains_credentials(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_credentials(item) for item in value)
    return False


def _is_loopback(hostname: str) -> bool:
    lowered = hostname.casefold().rstrip(".")
    if lowered in {"localhost", "localhost.localdomain"} or lowered.endswith(".localhost"):
        return True
    try:
        return ipaddress.ip_address(lowered).is_loopback
    except ValueError:
        return False


def _projection(plan: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None, tuple[str, ...]]:
    diagnostics: list[str] = []
    servers: dict[str, dict[str, str]] = {}
    tool_ids: set[str] = set()
    exposed_names: set[tuple[str, str]] = set()
    codex_target = False
    tools = plan.get("tools")
    if not isinstance(tools, list):
        return None, None, ("mcp.tools_invalid",)

    for tool in tools:
        if not isinstance(tool, dict):
            continue
        realizations = tool.get("realizations")
        remote = [
            item for item in realizations
            if isinstance(item, dict) and item.get("mechanism") == "MCP_REMOTE_HTTPS"
        ] if isinstance(realizations, list) else []
        if not remote:
            continue

        tool_id = tool.get("id")
        if not isinstance(tool_id, str) or _ID.fullmatch(tool_id) is None:
            diagnostics.append("mcp.tool_id_invalid")
        elif tool_id in tool_ids:
            diagnostics.append(f"mcp.tool_duplicate:{tool_id}")
        else:
            tool_ids.add(tool_id)

        mcp = tool.get("mcp")
        if not isinstance(mcp, dict):
            diagnostics.append(f"mcp.contract_missing:{tool_id}")
            continue
        server_id = mcp.get("server_id")
        label = str(server_id) if isinstance(server_id, str) else str(tool_id)
        if not isinstance(server_id, str) or _ID.fullmatch(server_id) is None:
            diagnostics.append(f"mcp.server_id_invalid:{label}")
            continue
        if _contains_credentials(mcp):
            diagnostics.append(f"mcp.credential_material_forbidden:{server_id}")
        if mcp.get("transport") != "streamable-http":
            diagnostics.append(f"mcp.transport_unsupported:{server_id}")
        if mcp.get("config_file") != "mcp.json" or not _safe_root_path(mcp.get("config_file")):
            diagnostics.append(f"mcp.config_path_invalid:{server_id}")

        url = mcp.get("url")
        parsed = urlsplit(url) if isinstance(url, str) else None
        if parsed is None or parsed.scheme != "https" or not parsed.hostname:
            diagnostics.append(f"mcp.url_https_required:{server_id}")
        else:
            if parsed.username is not None or parsed.password is not None:
                diagnostics.append(f"mcp.url_credentials_forbidden:{server_id}")
            if parsed.query:
                diagnostics.append(f"mcp.url_query_forbidden:{server_id}")
            if parsed.fragment:
                diagnostics.append(f"mcp.url_fragment_forbidden:{server_id}")
            if _is_loopback(parsed.hostname):
                diagnostics.append(f"mcp.remote_loopback_forbidden:{server_id}")

        for realization in remote:
            exposed = realization.get("exposed_capability")
            target = realization.get("target_runtime")
            if not isinstance(exposed, str) or not exposed:
                diagnostics.append(f"mcp.exposed_capability_invalid:{server_id}")
            elif (str(target), exposed) in exposed_names:
                diagnostics.append(f"mcp.exposed_capability_duplicate:{target}:{exposed}")
            else:
                exposed_names.add((str(target), exposed))
            if realization.get("transport") != "MCP_STREAMABLE_HTTP":
                diagnostics.append(f"mcp.realization_transport_invalid:{server_id}")
            if target == "Codex":
                codex_target = True
        if isinstance(url, str):
            server = {"type": "streamable-http", "url": url}
            if server_id in servers and servers[server_id] != server:
                diagnostics.append(f"mcp.server_duplicate:{server_id}")
            else:
                servers[server_id] = server

    if not servers:
        return None, None, tuple(sorted(set(diagnostics)))
    portable = {
        "$schema": MCP_SCHEMA,
        "mcpServers": {key: servers[key] for key in sorted(servers)},
    }
    decision = plan.get("implementation_decisions")
    profile = decision.get("manifest_profile") if isinstance(decision, dict) else None
    compatibility_required = codex_target and isinstance(profile, dict) and profile.get("target") == "OPENAI_DESKTOP"
    compatibility = json.loads(json.dumps(portable)) if compatibility_required else None
    return portable, compatibility, tuple(sorted(set(diagnostics)))


def expected_mcp_members(plan: dict[str, Any]) -> frozenset[str]:
    portable, compatibility, _diagnostics = _projection(plan)
    members: set[str] = set()
    if portable is not None:
        members.add("mcp.json")
    if compatibility is not None:
        members.add(".mcp.json")
    return frozenset(members)


def project_mcp_configuration(plan: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    portable, compatibility, diagnostics = _projection(plan)
    if diagnostics:
        raise ValueError(diagnostics[0])
    return portable, compatibility


def validate_mcp_projection(plan: dict[str, Any], tree: Path) -> tuple[str, ...]:
    portable, compatibility, diagnostics = _projection(plan)
    errors = list(diagnostics)
    expected = plan.get("expected_members")
    declared = set(expected) if isinstance(expected, list) else set()
    projections = {"mcp.json": portable, ".mcp.json": compatibility}
    root = Path(tree)
    for name, payload in projections.items():
        path = root / name
        if payload is None:
            if path.exists():
                errors.append(f"mcp.generated_member_unexpected:{name}")
            continue
        if name not in declared:
            errors.append(f"mcp.generated_member_undeclared:{name}")
        if not path.is_file():
            errors.append(f"mcp.generated_member_missing:{name}")
            continue
        try:
            actual = path.read_bytes()
        except OSError:
            errors.append(f"mcp.generated_member_unreadable:{name}")
            continue
        if actual != canonical_mcp_bytes(payload):
            label = "portable" if name == "mcp.json" else "compatibility"
            errors.append(f"mcp.{label}_projection_mismatch")
    return tuple(sorted(set(errors)))


__all__ = [
    "MCP_SCHEMA",
    "canonical_mcp_bytes",
    "expected_mcp_members",
    "project_mcp_configuration",
    "validate_mcp_projection",
]
