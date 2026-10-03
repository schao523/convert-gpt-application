from __future__ import annotations

from dataclasses import replace
from importlib.resources import files
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from obvious_one_plugin_framework.contract import PublicationProfile, PublicationTarget
from obvious_one_plugin_framework.marketplace import (
    MarketplaceError,
    PreparationCatalog,
    PreparationTarget,
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
                {
                    "name": entry.application.plugin_id,
                    "source": {"path": f"./{entry.target('codex').destination}"},
                }
                for entry in plan.applications
                if entry.target("codex").mode != "not_applicable"
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
                if entry.target("openclaw").mode != "not_applicable"
            ]
        }
        return codex, openclaw

    def codex_only_catalog(self) -> PreparationCatalog:
        self.fixture._write_v2_catalog()
        return load_preparation_catalog(
            self.fixture.catalog_path, self.fixture.repository
        )

    def test_registry_contains_every_runtime_catalog_plugin_once(self) -> None:
        codex, openclaw = self.catalogs()

        registry = build_validation_registry(codex, openclaw, self.catalog)

        self.assertEqual(
            [item["plugin_id"] for item in registry["plugins"]],
            ["legacy", "modern"],
        )
        self.assertEqual(registry["schema_version"], 2)
        self.assertEqual(
            registry["plugins"][0]["targets"]["codex"]["mode"],
            "verify_existing",
        )
        self.assertEqual(
            registry["plugins"][1]["targets"]["openclaw"]["mode"],
            "build",
        )
        self.assertEqual(registry["plugins"][1]["clawhub"]["state"], "NOT APPLICABLE")

    def test_registry_accepts_codex_only_and_dual_runtime_plugin_sets(self) -> None:
        dual_codex, dual_openclaw = self.catalogs()
        dual = build_validation_registry(dual_codex, dual_openclaw, self.catalog)
        codex_only_catalog = self.codex_only_catalog()
        codex, openclaw = self.catalogs(codex_only_catalog)

        asymmetric = build_validation_registry(codex, openclaw, codex_only_catalog)

        self.assertEqual(len(dual["plugins"]), 2)
        self.assertEqual(
            [item["plugin_id"] for item in asymmetric["plugins"]],
            ["legacy", "modern"],
        )
        self.assertEqual(
            [item["name"] for item in openclaw["plugins"]],
            ["legacy"],
        )

    def test_registry_marks_excluded_target_not_applicable_without_path_or_artifact(self) -> None:
        catalog = self.codex_only_catalog()
        codex, openclaw = self.catalogs(catalog)

        registry = build_validation_registry(codex, openclaw, catalog)

        modern = next(item for item in registry["plugins"] if item["plugin_id"] == "modern")
        self.assertEqual(modern["targets"]["openclaw"], {"state": "NOT APPLICABLE"})

    def test_adding_plugin_expands_registry_without_workflow_edit(self) -> None:
        extra = replace(
            self.catalog.applications[1],
            application=replace(
                self.catalog.applications[1].application,
                application_id="synthetic",
                plugin_id="synthetic",
            ),
            contract=replace(self.catalog.applications[1].contract, plugin_id="synthetic"),
            codex=PreparationTarget("build", "plugins/synthetic"),
            openclaw=PreparationTarget("build", "openclaw/synthetic"),
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
                with self.assertRaisesRegex(MarketplaceError, "runtime_catalog_"):
                    build_validation_registry(codex, candidate, self.catalog)

    def test_missing_unexpected_duplicate_wrong_path_or_wrong_version_target_entry_fails(self) -> None:
        catalog = self.codex_only_catalog()
        codex, openclaw = self.catalogs(catalog)
        cases = []
        missing = json.loads(json.dumps(codex))
        missing["plugins"].pop()
        cases.append((missing, openclaw, "runtime_catalog_missing_entry"))
        unexpected = json.loads(json.dumps(openclaw))
        unexpected["plugins"].append(
            {"name": "unexpected", "version": "1.0.0", "source": "./openclaw/unexpected"}
        )
        cases.append((codex, unexpected, "runtime_catalog_unexpected_entry"))
        duplicate = json.loads(json.dumps(codex))
        duplicate["plugins"].append(dict(duplicate["plugins"][0]))
        cases.append((duplicate, openclaw, "runtime_catalog_target_mismatch"))
        wrong_path = json.loads(json.dumps(codex))
        wrong_path["plugins"][1]["source"]["path"] = "./plugins/wrong"
        cases.append((wrong_path, openclaw, "runtime_catalog_target_mismatch"))
        wrong_version = json.loads(json.dumps(openclaw))
        wrong_version["plugins"][0]["version"] = "9.9.9"
        cases.append((codex, wrong_version, "runtime_catalog_target_mismatch"))

        for codex_candidate, openclaw_candidate, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                with self.assertRaises(MarketplaceError) as raised:
                    build_validation_registry(codex_candidate, openclaw_candidate, catalog)
                self.assertEqual(raised.exception.code, diagnostic)

    def test_command_for_not_applicable_target_is_rejected(self) -> None:
        conversion = self.fixture._conversion(self.fixture.modern)
        conversion["verification"]["commands"][0]["marketplace_targets"] = ["openclaw"]
        self.fixture._write_v2_catalog()
        from tests.framework.test_verification_config import _write_json

        _write_json(self.fixture.modern / "conversion.json", conversion)
        catalog = load_preparation_catalog(
            self.fixture.catalog_path, self.fixture.repository
        )
        codex, openclaw = self.catalogs(catalog)

        with self.assertRaisesRegex(MarketplaceError, "marketplace_command_target_not_applicable"):
            build_validation_registry(codex, openclaw, catalog)

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

    def test_enabled_native_clawhub_build_passes_generated_verifier(self) -> None:
        source = self.fixture.modern
        (source / "openclaw.plugin.json").write_text(
            json.dumps(
                {
                    "id": "modern",
                    "configSchema": {"type": "object", "additionalProperties": False},
                }
            ),
            encoding="utf-8",
        )
        (source / "index.js").write_text("export default {};\n", encoding="utf-8")
        (source / "package.json").write_text(
            json.dumps(
                {
                    "name": "@example/modern",
                    "version": "1.2.3",
                    "openclaw": {"extensions": ["./index.js"]},
                }
            ),
            encoding="utf-8",
        )
        contract_path = source / "openclaw" / "distribution.json"
        raw = json.loads(contract_path.read_text(encoding="utf-8"))
        raw["include_files"].extend(["openclaw.plugin.json", "index.js"])
        raw["content_rules"][0]["paths"].extend(
            ["openclaw.plugin.json", "index.js"]
        )
        raw["publication"]["clawhub"] = {
            "enabled": True,
            "family": "native-plugin",
            "native_manifest": "openclaw.plugin.json",
        }
        contract_path.write_text(json.dumps(raw), encoding="utf-8")
        catalog = load_preparation_catalog(
            self.fixture.catalog_path, self.fixture.repository
        )
        prepare_marketplace(catalog, self.fixture.baseline, self.fixture.output)

        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(self.fixture.output / "tools/verify_marketplace.py"),
                "--registry",
                str(self.fixture.output / ".obvious-one-validation.json"),
                "--plugin",
                "modern",
                "--json",
            ],
            cwd=self.fixture.output,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["status"], "PASS")

    def test_packaged_verifier_template_is_loaded_from_resources(self) -> None:
        resource = files("obvious_one_plugin_framework").joinpath(
            "templates/marketplace/verify_marketplace.py.template"
        )
        self.assertTrue(resource.is_file())
        self.assertEqual(render_marketplace_verifier(), resource.read_text(encoding="utf-8"))

    def test_generated_verifier_validates_stage_and_detects_legacy_drift(self) -> None:
        prepare_marketplace(self.catalog, self.fixture.baseline, self.fixture.output)
        self.assertTrue(
            (self.fixture.output / ".agents/plugins/marketplace.json").is_file()
        )
        self.assertTrue(
            (self.fixture.output / ".claude-plugin/marketplace.json").is_file()
        )
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

    def test_generated_verifier_rejects_runtime_catalog_drift(self) -> None:
        catalog = self.codex_only_catalog()
        prepare_marketplace(catalog, self.fixture.baseline, self.fixture.output)
        command = [
            sys.executable,
            "-B",
            str(self.fixture.output / "tools/verify_marketplace.py"),
            "--registry",
            str(self.fixture.output / ".obvious-one-validation.json"),
            "--plugin",
            "modern",
            "--json",
        ]
        codex_path = self.fixture.output / ".agents/plugins/marketplace.json"
        openclaw_path = self.fixture.output / ".claude-plugin/marketplace.json"
        original_codex = codex_path.read_bytes()
        original_openclaw = openclaw_path.read_bytes()
        cases = {
            "missing-codex": (
                codex_path,
                {"plugins": []},
            ),
            "phantom-openclaw": (
                openclaw_path,
                {
                    "plugins": [
                        {
                            "name": "legacy",
                            "version": "1.0.0",
                            "source": "./openclaw/legacy",
                        },
                        {
                            "name": "modern",
                            "version": "1.2.3",
                            "source": "./openclaw/modern",
                        },
                    ]
                },
            ),
        }
        try:
            for name, (path, payload) in cases.items():
                with self.subTest(name):
                    path.write_text(json.dumps(payload), encoding="utf-8")
                    completed = subprocess.run(
                        command,
                        cwd=self.fixture.output,
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(completed.returncode, 0)
                    self.assertEqual(
                        json.loads(completed.stdout)["code"],
                        "runtime_catalog_mismatch",
                    )
                    codex_path.write_bytes(original_codex)
                    openclaw_path.write_bytes(original_openclaw)
        finally:
            codex_path.write_bytes(original_codex)
            openclaw_path.write_bytes(original_openclaw)

    def test_generated_verifier_does_not_retrust_stale_legacy_manifest(self) -> None:
        manifest_path = self.fixture.baseline / "openclaw/legacy/CONTENT-MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"][0]["sha256"] = "0" * 64
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(MarketplaceError, "content_manifest_mismatch"):
            prepare_marketplace(self.catalog, self.fixture.baseline, self.fixture.output)

        self.assertFalse(self.fixture.output.exists())

    def test_generated_verifier_rejects_windows_drive_relative_registry_paths(self) -> None:
        prepare_marketplace(self.catalog, self.fixture.baseline, self.fixture.output)
        registry_path = self.fixture.output / ".obvious-one-validation.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["plugins"][1]["targets"]["codex"]["path"] = "C:outside"
        registry_path.write_text(json.dumps(registry), encoding="utf-8")

        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(self.fixture.output / "tools/verify_marketplace.py"),
                "--registry",
                str(registry_path),
                "--plugin",
                "modern",
                "--json",
            ],
            cwd=self.fixture.output,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout)["code"], "registry_path_escape")

    def test_generated_verifier_rejects_non_v2_registry(self) -> None:
        prepare_marketplace(self.catalog, self.fixture.baseline, self.fixture.output)
        registry_path = self.fixture.output / ".obvious-one-validation.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["schema_version"] = 1
        registry_path.write_text(json.dumps(registry), encoding="utf-8")

        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(self.fixture.output / "tools/verify_marketplace.py"),
                "--registry",
                str(registry_path),
                "--plugin",
                "modern",
                "--json",
            ],
            cwd=self.fixture.output,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout)["code"], "invalid_registry")

    def test_generated_verifier_runs_only_applicable_targets(self) -> None:
        catalog = self.codex_only_catalog()

        with patch("obvious_one_plugin_framework.marketplace._merge_exact_byte_attributes"):
            prepare_marketplace(catalog, self.fixture.baseline, self.fixture.output)

        self.assertFalse((self.fixture.output / "openclaw/modern").exists())
        registry = json.loads(
            (self.fixture.output / ".obvious-one-validation.json").read_text(encoding="utf-8")
        )
        modern = next(item for item in registry["plugins"] if item["plugin_id"] == "modern")
        self.assertEqual(modern["targets"]["openclaw"], {"state": "NOT APPLICABLE"})
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(self.fixture.output / "tools/verify_marketplace.py"),
                "--registry",
                str(self.fixture.output / ".obvious-one-validation.json"),
                "--plugin",
                "modern",
                "--json",
            ],
            cwd=self.fixture.output,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
