from __future__ import annotations

from pathlib import Path
import unittest

from obvious_one_plugin_framework.adapters import (
    AdapterContractError,
    DiscoveryRequest,
    IngestionRequest,
    validate_discovery_results,
    validate_ingestion_request,
)


class AdapterContractTests(unittest.TestCase):
    def test_ingestion_requires_owned_namespace(self) -> None:
        request = IngestionRequest(
            plugin_id="plugin-alpha",
            app_id="plugin-alpha",
            namespace="plugin-beta:docs",
            source_manifest=Path("source-manifest.json"),
            chunker_id="paragraph-v1",
            chunker_config_sha256="a" * 64,
            model_id="example/model",
            model_revision="revision-1",
            dimensions=8,
            destination_index=Path("index.sqlite3"),
        )
        with self.assertRaisesRegex(AdapterContractError, "namespace_owner_mismatch"):
            validate_ingestion_request(request)

    def test_discovery_rejects_cross_plugin_result(self) -> None:
        request = DiscoveryRequest(
            plugin_id="plugin-alpha",
            app_id="plugin-alpha",
            namespace="plugin-alpha:docs",
            query="grace",
            filters={"kind": "source"},
            limit=5,
            corpus_identity="corpus-a",
            model_identity="model-a",
        )
        results = [{
            "app_id": "plugin-beta",
            "namespace": "plugin-beta:docs",
            "metadata": {"app_id": "plugin-beta"},
        }]
        with self.assertRaisesRegex(AdapterContractError, "cross_plugin_result"):
            validate_discovery_results(request, results)

    def test_discovery_accepts_scoped_object_results(self) -> None:
        class Chunk:
            namespace = "plugin-alpha:docs"
            metadata = {"app_id": "plugin-alpha"}
        class Result:
            chunk = Chunk()
        request = DiscoveryRequest(
            "plugin-alpha", "plugin-alpha", "plugin-alpha:docs", "grace",
            {}, 1, "corpus-a", "model-a",
        )
        validate_discovery_results(request, [Result()])


if __name__ == "__main__":
    unittest.main()
