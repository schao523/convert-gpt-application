from __future__ import annotations

from hashlib import sha256
from pathlib import Path, PurePosixPath
import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest

from scripts import write_extraction_provenance as provenance_cli

from obvious_one_plugin_framework.provenance import (
    ProvenanceError,
    build_provenance,
    inventory_source,
    validate_provenance,
)
from obvious_one_plugin_framework.verification import (
    ApplicationConfig,
    ApplicationVerificationProfile,
    CodexBuildProfile,
    ProvenanceInventoryRule,
    ProvenanceProfile,
)


def _git_repository(path: Path, filename: str) -> str:
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    (path / filename).write_text(filename + "\n", encoding="utf-8")
    subprocess.run(["git", "add", filename], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=path, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()


def _config(root: Path) -> ApplicationConfig:
    application = root / "applications" / "plugin-alpha"
    return ApplicationConfig(
        root=application,
        application_id="plugin-alpha",
        plugin_id="plugin-alpha",
        version="1.0.0",
        source_inventory=root / "docs" / "source.json",
        source_location=application / "conversion.local.json",
        coverage_matrix=application / "tests" / "coverage-matrix.md",
        distribution_contract=application / "openclaw" / "distribution.json",
        marketplace_repository="schao523/obvious-one-plugins",
        provenance=ProvenanceProfile(
            source_repository="plugin-alpha-gpt-source",
            incorporated_branches=("feature/import",),
            inventory_rules=(
                ProvenanceInventoryRule(
                    PurePosixPath("."), "source-only", ("*.pdf", "*_guide.md")
                ),
                ProvenanceInventoryRule(
                    PurePosixPath("plugin-alpha/assets"),
                    "public-product-asset",
                    ("**/*",),
                ),
            ),
        ),
        verification=ApplicationVerificationProfile(
            test_directory=application / "tests",
            commands=(),
            codex_build=CodexBuildProfile(("{python}",), "plugins/{plugin_id}"),
            marketplace=None,
        ),
    )


class ProvenanceGenerationTests(unittest.TestCase):
    def test_non_git_source_uses_content_addressed_tree_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            marketplace = root / "marketplace"
            source.mkdir()
            (source / "source.pdf").write_bytes(b"source archive")
            _git_repository(marketplace, "catalog.json")

            payload = build_provenance(_config(root), source, marketplace)

            self.assertEqual(payload["schema_version"], 3)
            self.assertNotIn("source_commit", payload)
            self.assertRegex(str(payload["source_tree_sha256"]), r"^[0-9a-f]{64}$")
            validate_provenance(payload, _config(root))

    def test_builds_sorted_rule_driven_record_with_configured_identities(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            marketplace = root / "marketplace"
            source_commit = _git_repository(source, "source.pdf")
            marketplace_commit = _git_repository(marketplace, "catalog.json")
            (source / "notes.txt").write_text("excluded\n", encoding="utf-8")
            (source / "study_guide.md").write_text("guide\n", encoding="utf-8")
            assets = source / "plugin-alpha" / "assets"
            assets.mkdir(parents=True)
            (assets / "資料.txt").write_text("portable\n", encoding="utf-8")

            payload = build_provenance(_config(root), source, marketplace)

            self.assertEqual(payload["schema_version"], 2)
            self.assertEqual(payload["application_id"], "plugin-alpha")
            self.assertEqual(payload["plugin_id"], "plugin-alpha")
            self.assertEqual(payload["source_repository"], "plugin-alpha-gpt-source")
            self.assertEqual(payload["marketplace_repository"], "schao523/obvious-one-plugins")
            self.assertEqual(payload["source_commit"], source_commit)
            self.assertEqual(payload["marketplace_commit"], marketplace_commit)
            self.assertEqual(payload["incorporated_branches"], ["feature/import"])
            self.assertEqual(
                [(item["classification"], item["path"]) for item in payload["source_inventory"]],
                [
                    ("public-product-asset", "plugin-alpha/assets/資料.txt"),
                    ("source-only", "source.pdf"),
                    ("source-only", "study_guide.md"),
                ],
            )
            self.assertEqual(
                payload["source_inventory"][1]["sha256"],
                sha256((source / "source.pdf").read_bytes()).hexdigest(),
            )
            validate_provenance(payload, _config(root))

    def test_inventory_rejects_rule_root_outside_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            source.mkdir()
            rule = ProvenanceInventoryRule(
                PurePosixPath("../outside"), "source-only", ("**/*",)
            )
            with self.assertRaisesRegex(ProvenanceError, "inventory_root_escape"):
                inventory_source(source, (rule,))


class ProvenanceValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path("repository")
        self.config = _config(self.root)
        self.payload = {
            "schema_version": 2,
            "application_id": "plugin-alpha",
            "plugin_id": "plugin-alpha",
            "source_repository": "plugin-alpha-gpt-source",
            "source_commit": "1" * 40,
            "marketplace_repository": "schao523/obvious-one-plugins",
            "marketplace_commit": "2" * 40,
            "incorporated_branches": ["feature/import"],
            "source_inventory": [
                {
                    "classification": "source-only",
                    "path": "source.pdf",
                    "sha256": "3" * 64,
                }
            ],
        }

    def test_rejects_application_identity_mismatch(self) -> None:
        self.payload["application_id"] = "plugin-beta"
        with self.assertRaisesRegex(ProvenanceError, "application_identity_mismatch"):
            validate_provenance(self.payload, self.config)

    def test_schema_version_requires_an_exact_supported_integer(self) -> None:
        for value in (True, 1.0, "2", None):
            with self.subTest(value=value):
                payload = {**self.payload, "schema_version": value}
                with self.assertRaisesRegex(ProvenanceError, "unsupported_schema_version"):
                    validate_provenance(payload, self.config)

    def test_rejects_unknown_top_level_and_inventory_fields(self) -> None:
        top_level = {**self.payload, "private_source_path": "D:/private/source"}
        with self.assertRaisesRegex(ProvenanceError, "unknown_provenance_field"):
            validate_provenance(top_level, self.config)

        inventory = dict(self.payload["source_inventory"][0])
        inventory["absolute_path"] = "D:/private/source.pdf"
        payload = {**self.payload, "source_inventory": [inventory]}
        with self.assertRaisesRegex(ProvenanceError, "unknown_inventory_field"):
            validate_provenance(payload, self.config)

    def test_rejects_marketplace_identity_mismatch(self) -> None:
        self.payload["marketplace_repository"] = "example/other"
        with self.assertRaisesRegex(ProvenanceError, "marketplace_identity_mismatch"):
            validate_provenance(self.payload, self.config)

    def test_rejects_duplicate_inventory_paths(self) -> None:
        self.payload["source_inventory"].append(dict(self.payload["source_inventory"][0]))
        with self.assertRaisesRegex(ProvenanceError, "duplicate_inventory_path"):
            validate_provenance(self.payload, self.config)

    def test_rejects_malformed_digest_and_escaping_path(self) -> None:
        cases = (("sha256", "bad", "invalid_inventory_digest"), ("path", "../secret", "inventory_path_escape"))
        for field, value, error in cases:
            with self.subTest(field=field):
                payload = {**self.payload, "source_inventory": [dict(self.payload["source_inventory"][0])]}
                payload["source_inventory"][0][field] = value
                with self.assertRaisesRegex(ProvenanceError, error):
                    validate_provenance(payload, self.config)

    def test_rejects_dot_inventory_path(self) -> None:
        payload = {**self.payload, "source_inventory": [dict(self.payload["source_inventory"][0])]}
        payload["source_inventory"][0]["path"] = "."
        with self.assertRaisesRegex(ProvenanceError, "invalid_inventory_path"):
            validate_provenance(payload, self.config)

    def test_rejects_whitespace_inventory_classification(self) -> None:
        payload = {**self.payload, "source_inventory": [dict(self.payload["source_inventory"][0])]}
        payload["source_inventory"][0]["classification"] = "   "
        with self.assertRaisesRegex(ProvenanceError, "invalid_inventory_classification"):
            validate_provenance(payload, self.config)


class ProvenanceCliTests(unittest.TestCase):
    def test_parser_requires_application_and_accepts_configured_inputs(self) -> None:
        options = provenance_cli.build_parser().parse_args(
            [
                "--application",
                "plugin-alpha",
                "--source",
                "source",
                "--marketplace",
                "marketplace",
            ]
        )
        self.assertEqual(options.application, "plugin-alpha")
        self.assertEqual(options.source, Path("source"))

    def test_output_override_must_remain_in_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp).resolve()
            config = _config(repository)
            self.assertEqual(
                provenance_cli.resolve_output(config, repository, None),
                config.source_inventory.resolve(),
            )
            with self.assertRaisesRegex(ValueError, "output_path_escape"):
                provenance_cli.resolve_output(
                    config,
                    repository,
                    repository.parent / "outside.json",
                )

    def test_main_discovers_application_and_writes_valid_configured_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repository = root / "repository"
            application = repository / "applications" / "plugin-beta"
            fixture = Path(__file__).parents[1] / "fixtures" / "verification" / "plugin-beta"
            shutil.copytree(fixture, application)
            docs = repository / "docs"
            docs.mkdir()
            output = docs / "plugin-beta-source.json"
            output.write_text("{}\n", encoding="utf-8")
            source = root / "source"
            marketplace = root / "marketplace"
            _git_repository(source, "source.md")
            _git_repository(marketplace, "catalog.json")

            with contextlib.redirect_stdout(io.StringIO()):
                code = provenance_cli.main(
                    [
                        "--application",
                        "plugin-beta",
                        "--source",
                        str(source),
                        "--marketplace",
                        str(marketplace),
                    ],
                    repository_root=repository,
                )

            self.assertEqual(code, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            from obvious_one_plugin_framework.verification import load_application_config

            validate_provenance(payload, load_application_config(application, repository))


if __name__ == "__main__":
    unittest.main()
