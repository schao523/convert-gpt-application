"""Identity and scope contracts for generic RAG ingestion and discovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Mapping, Sequence


_DIGEST = re.compile(r"^[0-9a-f]{64}$")


class AdapterContractError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code if not detail else f"{code}: {detail}")
        self.code = code


@dataclass(frozen=True)
class IngestionRequest:
    plugin_id: str
    app_id: str
    namespace: str
    source_manifest: Path
    chunker_id: str
    chunker_config_sha256: str
    model_id: str
    model_revision: str
    dimensions: int
    destination_index: Path


@dataclass(frozen=True)
class DiscoveryRequest:
    plugin_id: str
    app_id: str
    namespace: str
    query: str
    filters: Mapping[str, str]
    limit: int
    corpus_identity: str
    model_identity: str


def _identity(plugin_id: str, app_id: str, namespace: str) -> None:
    if not plugin_id or not app_id or not namespace:
        raise AdapterContractError("identity_required")
    if plugin_id != app_id:
        raise AdapterContractError("plugin_app_mismatch")
    if not namespace.startswith(app_id + ":"):
        raise AdapterContractError("namespace_owner_mismatch", namespace)


def validate_ingestion_request(request: IngestionRequest) -> None:
    _identity(request.plugin_id, request.app_id, request.namespace)
    if not request.chunker_id or not request.model_id or not request.model_revision:
        raise AdapterContractError("ingestion_identity_required")
    if not _DIGEST.fullmatch(request.chunker_config_sha256.lower()):
        raise AdapterContractError("invalid_chunker_digest")
    if request.dimensions <= 0:
        raise AdapterContractError("invalid_dimensions")
    if not str(request.source_manifest) or not str(request.destination_index):
        raise AdapterContractError("ingestion_path_required")


def validate_discovery_request(request: DiscoveryRequest) -> None:
    _identity(request.plugin_id, request.app_id, request.namespace)
    if not request.query.strip():
        raise AdapterContractError("query_required")
    if request.limit <= 0:
        raise AdapterContractError("invalid_limit")
    if not request.corpus_identity or not request.model_identity:
        raise AdapterContractError("retrieval_identity_required")
    filter_app = request.filters.get("app_id")
    if filter_app is not None and filter_app != request.app_id:
        raise AdapterContractError("filter_app_mismatch")


def _result_identity(result: object) -> tuple[object, object]:
    if isinstance(result, Mapping):
        chunk = result
    else:
        chunk = getattr(result, "chunk", result)
    if isinstance(chunk, Mapping):
        metadata = chunk.get("metadata", {})
        app_id = chunk.get("app_id")
        namespace = chunk.get("namespace")
    else:
        metadata = getattr(chunk, "metadata", {})
        app_id = getattr(chunk, "app_id", None)
        namespace = getattr(chunk, "namespace", None)
    if isinstance(metadata, Mapping):
        app_id = metadata.get("app_id", app_id)
    return app_id, namespace


def validate_discovery_results(
    request: DiscoveryRequest,
    results: Sequence[object],
) -> None:
    validate_discovery_request(request)
    for index, result in enumerate(results):
        app_id, namespace = _result_identity(result)
        if app_id != request.app_id or namespace != request.namespace:
            raise AdapterContractError(
                "cross_plugin_result",
                f"result {index} has app_id={app_id!r}, namespace={namespace!r}",
            )
