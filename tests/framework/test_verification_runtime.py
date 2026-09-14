from __future__ import annotations

from dataclasses import replace
from pathlib import Path, PurePosixPath
import sys
import tempfile
import unittest

from obvious_one_plugin_framework.verification import (
    ApplicationConfig,
    ApplicationVerificationProfile,
    CodexBuildProfile,
    ExpansionContext,
    GateResult,
    ProvenanceInventoryRule,
    ProvenanceProfile,
    VerificationConfigError,
    aggregate_state,
    expand_argv,
    resolve_within,
    select_applications,
)


def _config(root: Path, application_id: str) -> ApplicationConfig:
    application = root / "applications" / application_id
    return ApplicationConfig(
        root=application,
        application_id=application_id,
        plugin_id=application_id,
        version="1.2.3",
        source_inventory=root / "docs" / "source.json",
        source_location=application / "conversion.local.json",
        coverage_matrix=application / "tests" / "coverage-matrix.md",
        distribution_contract=application / "openclaw" / "distribution.json",
        marketplace_repository="example/plugins",
        provenance=ProvenanceProfile(
            source_repository=f"{application_id}-source",
            incorporated_branches=(),
            inventory_rules=(
                ProvenanceInventoryRule(PurePosixPath("."), "source-only", ("*.md",)),
            ),
        ),
        verification=ApplicationVerificationProfile(
            test_directory=application / "tests",
            commands=(),
            codex_build=CodexBuildProfile(
                argv=("{python}",), artifact_path="plugins/{plugin_id}"
            ),
            marketplace=None,
        ),
    )


class SelectionTests(unittest.TestCase):
    def test_default_and_explicit_all_are_sorted(self) -> None:
        root = Path("repository")
        configs = (_config(root, "plugin-beta"), _config(root, "plugin-alpha"))

        default = select_applications(configs, application_id=None, select_all=False)
        explicit = select_applications(configs, application_id=None, select_all=True)

        self.assertEqual([item.application_id for item in default], ["plugin-alpha", "plugin-beta"])
        self.assertEqual(explicit, default)

    def test_selects_one_application(self) -> None:
        root = Path("repository")
        configs = (_config(root, "plugin-alpha"), _config(root, "plugin-beta"))

        selected = select_applications(
            configs, application_id="plugin-alpha", select_all=False
        )

        self.assertEqual([item.application_id for item in selected], ["plugin-alpha"])

    def test_rejects_unknown_or_conflicting_selection(self) -> None:
        configs = (_config(Path("repository"), "plugin-alpha"),)
        with self.assertRaisesRegex(VerificationConfigError, "unknown application"):
            select_applications(configs, application_id="missing", select_all=False)
        with self.assertRaisesRegex(VerificationConfigError, "mutually exclusive"):
            select_applications(configs, application_id="plugin-alpha", select_all=True)


class ExpansionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = Path("C:/repository").resolve()
        self.application = self.repository / "applications" / "plugin-alpha"
        self.diagnostics = self.repository / ".tmp" / "verification" / "run-1"
        self.context = ExpansionContext(
            python=sys.executable,
            repository_root=self.repository,
            application_root=self.application,
            diagnostics=self.diagnostics,
            plugin_id="plugin-alpha",
            application_id="plugin-alpha",
            version="1.2.3",
        )

    def test_expands_supported_placeholders_without_a_shell(self) -> None:
        argv = expand_argv(
            (
                "{python}",
                "-B",
                "{application_root}/scripts/smoke.py",
                "{repository_root}",
                "{diagnostics}",
                "{plugin_id}:{application_id}:{version}",
            ),
            self.context,
        )

        self.assertEqual(argv[0], sys.executable)
        self.assertEqual(argv[2], str(self.application / "scripts" / "smoke.py"))
        self.assertEqual(argv[-1], "plugin-alpha:plugin-alpha:1.2.3")
        self.assertIsInstance(argv, list)

    def test_rejects_unknown_malformed_or_empty_expansion(self) -> None:
        for argv, context in (
            (("{secret}",), self.context),
            (("{python",), self.context),
            (("{version}",), replace(self.context, version="")),
        ):
            with self.subTest(argv=argv), self.assertRaises(VerificationConfigError):
                expand_argv(argv, context)


class PathAndResultTests(unittest.TestCase):
    def test_resolves_only_paths_within_the_declared_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp).resolve()
            application = repository / "applications" / "plugin-alpha"
            diagnostics = repository / ".tmp" / "verification" / "run-1"
            marketplace = repository / "marketplace"

            self.assertEqual(
                resolve_within(application, "tests", field="test_directory"),
                application / "tests",
            )
            self.assertEqual(
                resolve_within(repository, "applications/plugin-alpha/../../docs/delta.json", field="approved_delta"),
                repository / "docs" / "delta.json",
            )
            self.assertEqual(
                resolve_within(diagnostics, "plugins/plugin-alpha", field="artifact"),
                diagnostics / "plugins" / "plugin-alpha",
            )
            self.assertEqual(
                resolve_within(marketplace, "plugins/plugin-alpha", field="marketplace"),
                marketplace / "plugins" / "plugin-alpha",
            )
            with self.assertRaisesRegex(VerificationConfigError, "escapes"):
                resolve_within(repository, "../outside", field="escape")
            with self.assertRaisesRegex(VerificationConfigError, "absolute"):
                resolve_within(repository, Path(temp).anchor, field="absolute")

    def test_gate_state_is_validated_and_aggregated(self) -> None:
        pass_gate = GateResult("tests", "PASS", "passed")
        not_verified = GateResult("marketplace", "NOT VERIFIED", "not supplied")
        not_applicable = GateResult("marketplace", "NOT APPLICABLE", "not configured")
        fail_gate = GateResult("build", "FAIL", "failed")

        self.assertEqual(aggregate_state([pass_gate, not_verified]), "PASS")
        self.assertEqual(aggregate_state([pass_gate, not_applicable]), "PASS")
        self.assertEqual(aggregate_state([pass_gate, fail_gate]), "FAIL")
        with self.assertRaisesRegex(ValueError, "invalid result state"):
            GateResult("bad", "SKIPPED", "unsupported")


if __name__ == "__main__":
    unittest.main()
