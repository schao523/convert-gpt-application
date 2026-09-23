from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _make_application(repository: Path, application_id: str = "plugin-alpha") -> Path:
    application = repository / "applications" / application_id
    (application / ".codex-plugin").mkdir(parents=True)
    _write_json(
        application / ".codex-plugin" / "plugin.json",
        {"name": application_id, "version": "1.2.3"},
    )
    _write_json(
        application / "openclaw" / "distribution.json",
        {
            "schema_version": 1,
            "plugin_id": application_id,
            "package_name": f"@example/{application_id}",
            "family": "bundle-plugin",
            "version": "1.2.3",
            "source_root": "..",
            "include_files": [".codex-plugin/plugin.json"],
            "include_prefixes": ["skills"],
            "exclude_paths": ["private"],
            "max_total_bytes": 100000,
            "release_repository": "example/plugins",
            "release_tag_template": f"{application_id}-v{{version}}",
            "readme_overlay": None,
            "audit_hook": None,
            "rag": {
                "app_id": application_id,
                "namespace": f"{application_id}:default",
                "runtime_lock": "vendor/runtime-lock.json",
                "runtime_lock_digest": "0" * 64,
                "model_manifest": "assets/model.json",
                "model_digest": "1" * 64,
                "index_manifest": "assets/index.json",
                "asset_groups": [
                    {
                        "name": "index",
                        "archive_name": f"{application_id}-index-{{version}}.zip",
                        "source_paths": ["assets/index.sqlite3"],
                        "install_subdir": "indexes",
                    }
                ],
            },
        },
    )
    _write_json(repository / "docs" / "source.json", {"files": []})
    (application / "tests").mkdir()
    (application / "tests" / "coverage-matrix.md").write_text("# Coverage\n", encoding="utf-8")
    _write_json(
        application / "conversion.json",
        {
            "schema_version": 2,
            "application_id": application_id,
            "plugin_id": application_id,
            "source_inventory": "../../docs/source.json",
            "source_location": "conversion.local.json",
            "coverage_matrix": "tests/coverage-matrix.md",
            "distribution_contract": "openclaw/distribution.json",
            "marketplace_repository": "example/plugins",
            "provenance": {
                "source_repository": "plugin-alpha-gpt-source",
                "incorporated_branches": ["feature/source-import"],
                "inventory_rules": [
                    {
                        "root": ".",
                        "classification": "source-only",
                        "include": ["*.pdf", "*_guide.md"],
                    },
                    {
                        "root": f"applications/{application_id}/assets",
                        "classification": "public-product-asset",
                        "include": ["**/*"],
                    },
                ],
            },
            "verification": {
                "test_directory": "tests",
                "commands": [
                    {
                        "id": "smoke",
                        "argv": ["{python}", "-B", "{application_root}/scripts/smoke.py"],
                    }
                ],
                "codex_build": {
                    "argv": ["{python}", "-B", "{application_root}/scripts/build.py"],
                    "artifact_path": "plugins/{plugin_id}",
                },
            },
        },
    )
    return application


class VerificationConfigTests(unittest.TestCase):
    def _load(self, application: Path, repository: Path):
        from obvious_one_plugin_framework.verification import load_application_config

        return load_application_config(application, repository)

    def _conversion(self, application: Path) -> dict[str, object]:
        return json.loads((application / "conversion.json").read_text(encoding="utf-8"))

    def _write_conversion(self, application: Path, value: dict[str, object]) -> None:
        _write_json(application / "conversion.json", value)

    def test_loads_valid_schema_v2_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp)
            application = _make_application(repository)

            config = self._load(application, repository)

            self.assertEqual(config.application_id, "plugin-alpha")
            self.assertEqual(config.plugin_id, "plugin-alpha")
            self.assertEqual(config.version, "1.2.3")
            self.assertEqual(config.provenance.source_repository, "plugin-alpha-gpt-source")
            self.assertEqual(
                config.provenance.incorporated_branches,
                ("feature/source-import",),
            )
            self.assertEqual(config.provenance.inventory_rules[0].root.as_posix(), ".")
            self.assertEqual(
                config.provenance.inventory_rules[0].include,
                ("*.pdf", "*_guide.md"),
            )
            self.assertEqual(config.verification.commands[0].command_id, "smoke")
            self.assertEqual(
                config.verification.codex_build.artifact_path,
                "plugins/{plugin_id}",
            )
            self.assertIsNone(config.verification.marketplace)
            self.assertEqual(config.verification.commands[0].marketplace_targets, ())

    def test_marketplace_command_targets_are_explicit_and_portable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp)
            application = _make_application(repository)
            data = self._conversion(application)
            command = data["verification"]["commands"][0]  # type: ignore[index]
            command["marketplace_targets"] = ["codex", "openclaw"]
            self._write_conversion(application, data)

            config = self._load(application, repository)

            self.assertEqual(
                config.verification.commands[0].marketplace_targets,
                ("codex", "openclaw"),
            )

    def test_marketplace_command_targets_reject_duplicates_unknown_and_dev_roots(self) -> None:
        cases = (
            (["codex", "codex"], ["{python}"]),
            (["registry"], ["{python}"]),
            (["codex"], ["{python}", "{repository_root}/script.py"]),
            (["openclaw"], ["{python}", "{diagnostics}/script.py"]),
        )
        for targets, argv in cases:
            with self.subTest(targets=targets, argv=argv), tempfile.TemporaryDirectory() as temp:
                repository = Path(temp)
                application = _make_application(repository)
                data = self._conversion(application)
                command = data["verification"]["commands"][0]  # type: ignore[index]
                command["marketplace_targets"] = targets
                command["argv"] = argv
                self._write_conversion(application, data)

                with self.assertRaisesRegex(ValueError, r"conversion\.json.*marketplace"):
                    self._load(application, repository)

    def test_load_application_config_path_accepts_non_repository_layout(self) -> None:
        from obvious_one_plugin_framework.verification import load_application_config_path

        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            conventional = _make_application(workspace, "demo")
            relocated = workspace / "workspace" / "products" / "demo"
            relocated.parent.mkdir(parents=True)
            conventional.rename(relocated)
            data = json.loads((relocated / "conversion.json").read_text(encoding="utf-8"))
            data["source_inventory"] = "../../../docs/source.json"
            self._write_conversion(relocated, data)

            config = load_application_config_path(relocated / "conversion.json", workspace)

            self.assertEqual(config.application_id, "demo")
            self.assertEqual(config.root, relocated.resolve())
            with self.assertRaisesRegex(ValueError, "immediate applications child"):
                self._load(relocated, workspace)

    def test_missing_provenance_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp)
            application = _make_application(repository)
            data = self._conversion(application)
            del data["provenance"]
            self._write_conversion(application, data)

            with self.assertRaisesRegex(ValueError, r"conversion\.json.*provenance"):
                self._load(application, repository)

    def test_unsafe_provenance_inventory_rules_are_rejected(self) -> None:
        cases = (
            ("root", "../outside"),
            ("root", str(Path(tempfile.gettempdir()).resolve())),
            ("include", []),
            ("include", ["../private/*"]),
            ("include", ["/absolute/*"]),
        )
        for field, value in cases:
            with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as temp:
                repository = Path(temp)
                application = _make_application(repository)
                data = self._conversion(application)
                data["provenance"]["inventory_rules"][0][field] = value  # type: ignore[index]
                self._write_conversion(application, data)

                with self.assertRaisesRegex(ValueError, r"conversion\.json.*provenance"):
                    self._load(application, repository)

    def test_duplicate_provenance_inventory_rules_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp)
            application = _make_application(repository)
            data = self._conversion(application)
            rule = data["provenance"]["inventory_rules"][0]  # type: ignore[index]
            data["provenance"]["inventory_rules"] = [rule, rule]  # type: ignore[index]
            self._write_conversion(application, data)

            with self.assertRaisesRegex(ValueError, r"conversion\.json.*duplicate"):
                self._load(application, repository)

    def test_schema_v1_requires_migration(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp)
            application = _make_application(repository)
            data = self._conversion(application)
            data["schema_version"] = 1
            self._write_conversion(application, data)

            with self.assertRaisesRegex(ValueError, r"conversion\.json.*schema_version.*migrat"):
                self._load(application, repository)

    def test_missing_verification_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp)
            application = _make_application(repository)
            data = self._conversion(application)
            del data["verification"]
            self._write_conversion(application, data)

            with self.assertRaisesRegex(ValueError, r"conversion\.json.*verification"):
                self._load(application, repository)

    def test_invalid_command_types_and_empty_arguments_are_rejected(self) -> None:
        cases = (
            ("commands", "not-a-list"),
            ("commands", [{"id": "smoke", "argv": ["{python}", ""]}]),
            ("commands", [{"id": "smoke", "argv": "{python}"}]),
        )
        for field, value in cases:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temp:
                repository = Path(temp)
                application = _make_application(repository)
                data = self._conversion(application)
                data["verification"][field] = value  # type: ignore[index]
                self._write_conversion(application, data)

                with self.assertRaisesRegex(ValueError, r"conversion\.json.*commands"):
                    self._load(application, repository)

    def test_duplicate_command_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp)
            application = _make_application(repository)
            data = self._conversion(application)
            command = data["verification"]["commands"][0]  # type: ignore[index]
            data["verification"]["commands"] = [command, command]  # type: ignore[index]
            self._write_conversion(application, data)

            with self.assertRaisesRegex(ValueError, r"conversion\.json.*commands.*smoke"):
                self._load(application, repository)

    def test_unknown_placeholders_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp)
            application = _make_application(repository)
            data = self._conversion(application)
            data["verification"]["commands"][0]["argv"] = ["{python}", "{secret}"]  # type: ignore[index]
            self._write_conversion(application, data)

            with self.assertRaisesRegex(ValueError, r"conversion\.json.*commands.*secret"):
                self._load(application, repository)

    def test_directory_application_and_plugin_identity_must_match(self) -> None:
        for field in ("application_id", "plugin_id"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                repository = Path(temp)
                application = _make_application(repository)
                data = self._conversion(application)
                data[field] = "different"
                self._write_conversion(application, data)

                with self.assertRaisesRegex(ValueError, rf"conversion\.json.*{field}"):
                    self._load(application, repository)

    def test_missing_distribution_contract_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp)
            application = _make_application(repository)
            (application / "openclaw" / "distribution.json").unlink()

            with self.assertRaisesRegex(ValueError, r"conversion\.json.*distribution_contract"):
                self._load(application, repository)

    def test_absolute_and_escaping_paths_are_rejected(self) -> None:
        for field, value in (
            ("test_directory", str(Path(tempfile.gettempdir()).resolve())),
            ("test_directory", "../../../outside"),
        ):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temp:
                repository = Path(temp)
                application = _make_application(repository)
                data = self._conversion(application)
                data["verification"][field] = value  # type: ignore[index]
                self._write_conversion(application, data)

                with self.assertRaisesRegex(ValueError, r"conversion\.json.*test_directory"):
                    self._load(application, repository)

    def test_discovery_rejects_duplicate_identity(self) -> None:
        from obvious_one_plugin_framework.verification import discover_applications

        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp)
            first = _make_application(repository, "plugin-alpha")
            second = _make_application(repository, "plugin-beta")
            data = self._conversion(second)
            data["application_id"] = "plugin-alpha"
            data["plugin_id"] = "plugin-alpha"
            self._write_conversion(second, data)

            with self.assertRaisesRegex(ValueError, r"conversion\.json.*application_id"):
                discover_applications(repository)


if __name__ == "__main__":
    unittest.main()
