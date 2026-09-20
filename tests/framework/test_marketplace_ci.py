from __future__ import annotations

from dataclasses import replace
from importlib.resources import files
import json
from pathlib import Path
import subprocess
import sys
import unittest

from obvious_one_plugin_framework.contract import PublicationProfile, PublicationTarget
from obvious_one_plugin_framework.marketplace import (
    MarketplaceError,
    PreparationCatalog,
    load_preparation_catalog,
    prepare_marketplace,
)
from obvious_one_plugin_framework.marketplace_ci import (
    build_validation_registry,
    render_marketplace_verifier,
    render_validation_workflow,
)
from tests.framework.test_marketplace import MarketplaceTests


class MarketplaceCiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = MarketplaceTests("test_build_requires_v3_and_verify_existing_accepts_legacy")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.catalog = load_preparation_catalog(
            self.fixture.catalog_path, self.fixture.repository
        )

    def catalogs(self, catalog: PreparationCatalog | None = None):
        plan = catalog or self.catalog
        codex = {
            "plugins": [
                {"name": entry.application.plugin_id, "source": {"path": f"./{entry.codex_destination}"}}
                for entry in plan.applications
            ]
        }
        openclaw = {
            "plugins": [
                {
                    "name": entry.application.plugin_id,
                    "version": entry.application.version,
                    "source": f"./{entry.openclaw_destination}",
                }
                for entry in plan.applications
            ]
        }
        return codex, openclaw

    def test_registry_contains_every_runtime_catalog_plugin_once(self) -> None:
        codex, openclaw = self.catalogs()

        registry = build_validation_registry(codex, openclaw, self.catalog)

        self.assertEqual(
            [item["plugin_id"] for item in registry["plugins"]],
            ["legacy", "modern"],
        )
        self.assertEqual(registry["plugins"][0]["mode"], "verify_existing")
        self.assertEqual(registry["plugins"][1]["mode"], "build")
        self.assertEqual(registry["plugins"][1]["clawhub"]["state"], "NOT APPLICABLE")

    def test_adding_plugin_expands_registry_without_workflow_edit(self) -> None:
        extra = replace(
            self.catalog.applications[1],
            application=replace(
                self.catalog.applications[1].application,
                application_id="synthetic",
                plugin_id="synthetic",
            ),
            contract=replace(self.catalog.applications[1].contract, plugin_id="synthetic"),
            codex_destination="plugins/synthetic",
            openclaw_destination="openclaw/synthetic",
        )
        plan = replace(self.catalog, applications=self.catalog.applications + (extra,))
        codex, openclaw = self.catalogs(plan)

        registry = build_validation_registry(codex, openclaw, plan)

        self.assertEqual(len(registry["plugins"]), 3)
        workflow = render_validation_workflow()
        self.assertNotIn("legacy", workflow)
        self.assertNotIn("modern", workflow)
        self.assertIn("matrix.plugin", workflow)

    def test_catalog_disagreement_missing_and_duplicate_entries_fail(self) -> None:
        codex, openclaw = self.catalogs()
        cases = []
        wrong = json.loads(json.dumps(openclaw))
        wrong["plugins"][1]["version"] = "9.9.9"
        cases.append(wrong)
        missing = json.loads(json.dumps(openclaw))
        missing["plugins"].pop()
        cases.append(missing)
        duplicate = json.loads(json.dumps(openclaw))
        duplicate["plugins"].append(dict(duplicate["plugins"][0]))
        cases.append(duplicate)
        for candidate in cases:
            with self.subTest(candidate=candidate):
                with self.assertRaisesRegex(MarketplaceError, "runtime_catalog_mismatch"):
                    build_validation_registry(codex, candidate, self.catalog)

    def test_enabled_clawhub_without_native_manifest_fails(self) -> None:
        modern = self.catalog.applications[1]
        publication = PublicationProfile(
            github_marketplace=PublicationTarget(True),
            clawhub=PublicationTarget(True, "native-plugin", None),
        )
        plan = replace(
            self.catalog,
            applications=(
                self.catalog.applications[0],
                replace(modern, contract=replace(modern.contract, publication=publication)),
            ),
        )
        codex, openclaw = self.catalogs(plan)

        with self.assertRaisesRegex(MarketplaceError, "clawhub_native_manifest_required"):
            build_validation_registry(codex, openclaw, plan)

    def test_packaged_verifier_template_is_loaded_from_resources(self) -> None:
        resource = files("obvious_one_plugin_framework").joinpath(
            "templates/marketplace/verify_marketplace.py.template"
        )
        self.assertTrue(resource.is_file())
        self.assertEqual(render_marketplace_verifier(), resource.read_text(encoding="utf-8"))

    def test_generated_verifier_validates_stage_and_detects_legacy_drift(self) -> None:
        prepare_marketplace(self.catalog, self.fixture.baseline, self.fixture.output)
        command = [
            sys.executable,
            "-B",
            str(self.fixture.output / "tools/verify_marketplace.py"),
            "--registry",
            str(self.fixture.output / ".obvious-one-validation.json"),
            "--plugin",
            "legacy",
            "--json",
        ]

        passed = subprocess.run(command, cwd=self.fixture.output, capture_output=True, text=True)
        self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
        self.assertEqual(json.loads(passed.stdout)["status"], "PASS")

        (self.fixture.output / "openclaw/legacy/README.md").write_bytes(b"drift\n")
        failed = subprocess.run(command, cwd=self.fixture.output, capture_output=True, text=True)
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(json.loads(failed.stdout)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
