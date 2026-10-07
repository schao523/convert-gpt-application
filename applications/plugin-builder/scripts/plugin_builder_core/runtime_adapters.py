"""Immutable, target-aware runtime adapter registry."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any


@dataclass(frozen=True, order=True)
class AdapterDefinition:
    adapter_id: str
    adapter_version: str
    mechanism: str
    transport: str
    execution_location: str
    runtime_targets: tuple[str, ...]
    installation_channels: tuple[str, ...]
    verification_channels: tuple[str, ...]
    configuration_files: tuple[str, ...]
    dependency_providers: tuple[str, ...]
    permission_ids: tuple[str, ...]
    evidence_layers: tuple[str, ...]
    endpoint_policy: str


_PHASE_ONE_TARGETS = ("ChatGPT Work Local/Desktop", "Codex")
_REGISTRY = tuple(sorted((
    AdapterDefinition(
        adapter_id="direct-local",
        adapter_version="1",
        mechanism="DIRECT_LOCAL",
        transport="DIRECT_ARGV",
        execution_location="USER_DEVICE",
        runtime_targets=_PHASE_ONE_TARGETS,
        installation_channels=(),
        verification_channels=("PLUGIN_BUILDER_LOCAL_TEST",),
        configuration_files=(),
        dependency_providers=("BUNDLED", "OWNER_CONFIGURED"),
        permission_ids=("workspace:read", "workspace:write"),
        evidence_layers=("STRUCTURE", "OPERATION"),
        endpoint_policy="NOT_APPLICABLE",
    ),
    AdapterDefinition(
        adapter_id="mcp-streamable-http",
        adapter_version="1",
        mechanism="MCP_REMOTE_HTTPS",
        transport="MCP_STREAMABLE_HTTP",
        execution_location="REMOTE_SERVICE",
        runtime_targets=_PHASE_ONE_TARGETS,
        installation_channels=("OPENAI_PORTABLE_PLUGIN",),
        verification_channels=("PLUGIN_BUILDER_LOCAL_TEST",),
        configuration_files=("mcp.json", ".mcp.json"),
        dependency_providers=("REMOTE_SERVICE",),
        permission_ids=("network",),
        evidence_layers=("STRUCTURE", "OPERATION", "INSTALLED_REALIZATION"),
        endpoint_policy="HTTPS_ONLY",
    ),
    AdapterDefinition(
        adapter_id="runtime-native",
        adapter_version="1",
        mechanism="RUNTIME_NATIVE",
        transport="RUNTIME_API",
        execution_location="RUNTIME_HOST",
        runtime_targets=_PHASE_ONE_TARGETS,
        installation_channels=(),
        verification_channels=(),
        configuration_files=(),
        dependency_providers=("RUNTIME_PROVIDED",),
        permission_ids=("runtime:native",),
        evidence_layers=("STRUCTURE",),
        endpoint_policy="NOT_APPLICABLE",
    ),
    AdapterDefinition(
        adapter_id="unsupported",
        adapter_version="1",
        mechanism="UNSUPPORTED",
        transport="NONE",
        execution_location="RUNTIME_HOST",
        runtime_targets=_PHASE_ONE_TARGETS,
        installation_channels=(),
        verification_channels=(),
        configuration_files=(),
        dependency_providers=(),
        permission_ids=(),
        evidence_layers=("STRUCTURE",),
        endpoint_policy="NOT_APPLICABLE",
    ),
), key=lambda item: (item.adapter_id, item.adapter_version)))


def adapter_registry() -> tuple[AdapterDefinition, ...]:
    """Return the immutable registry in canonical identity order."""

    return _REGISTRY


def adapter_registry_sha256() -> str:
    """Return the SHA-256 of canonical, data-only adapter records."""

    records = [asdict(item) for item in _REGISTRY]
    encoded = json.dumps(records, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
    return sha256(encoded).hexdigest()


def validate_realization_against_registry(
    realization: dict[str, Any],
    *,
    installation_channel: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Validate declared adapter support without probing or inferring a runtime."""

    if not isinstance(realization, dict):
        return ("adapter.realization_invalid",), ()
    if not isinstance(installation_channel, str) or not installation_channel:
        return ("adapter.installation_channel_invalid",), ()

    adapter_id = realization.get("adapter_id")
    version = realization.get("adapter_version")
    if not isinstance(adapter_id, str) or not adapter_id:
        return ("adapter.id_invalid",), ()
    definitions = tuple(item for item in _REGISTRY if item.adapter_id == adapter_id)
    if not definitions:
        return (f"adapter.unknown:{adapter_id}",), ()
    definition = next((item for item in definitions if item.adapter_version == version), None)
    if definition is None:
        return (f"adapter.{adapter_id}.version_unsupported:{version}",), ()

    prefix = f"adapter.{adapter_id}"
    errors: list[str] = []
    blockers: list[str] = []
    if realization.get("mechanism") != definition.mechanism:
        errors.append(f"{prefix}.mechanism_mismatch")
    if realization.get("transport") != definition.transport:
        errors.append(f"{prefix}.transport_mismatch")
    if realization.get("execution_location") != definition.execution_location:
        errors.append(f"{prefix}.execution_location_mismatch")
    target = realization.get("target_runtime")
    if target not in definition.runtime_targets:
        errors.append(f"{prefix}.target_unsupported:{target}")

    if installation_channel in definition.verification_channels:
        blockers.append(f"{prefix}.verification_channel_not_installed")
    elif installation_channel not in definition.installation_channels:
        blockers.append(f"{prefix}.channel_unsupported:{installation_channel}")

    return tuple(sorted(set(errors))), tuple(sorted(set(blockers)))
