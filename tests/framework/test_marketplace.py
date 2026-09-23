from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tests.framework.test_verification_config import _make_application, _write_json

from obvious_one_plugin_framework.marketplace import (
    MarketplaceError,
    _reject_links,
    load_preparation_catalog,
    prepare_marketplace,
    verify_marketplace,
)


class MarketplaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repository = self.root / "repository"
        self.baseline = self.root / "baseline"
        self.output = self.root / "staged"
        self.repository.mkdir()
        self.baseline.mkdir()
        self.legacy = _make_application(self.repository, "legacy")
        self.modern = _make_application(self.repository, "modern")
        self._upgrade_to_v3(self.modern)
        self._add_codex_builder(self.modern)
        self._write_existing_legacy()
        (self.baseline / "untouched.txt").write_bytes(b"untouched\r\n")
        self.catalog_path = self.repository / "marketplace.json"
        self._write_catalog()

    def _conversion(self, application: Path) -> dict[str, object]:
        return json.loads((application / "conversion.json").read_text(encoding="utf-8"))

    def _write_catalog(self, *, modern_mode: str = "build") -> None:
        _write_json(
            self.catalog_path,
            {
                "schema_version": 1,
                "marketplace_id": "test-marketplace",
                "applications": [
                    {
                        "application_config": "applications/legacy/conversion.json",
                        "distribution_contract": "applications/legacy/openclaw/distribution.json",
                        "codex_destination": "plugins/legacy",
                        "openclaw_destination": "openclaw/legacy",
                        "mode": "verify_existing",
                    },
                    {
                        "application_config": "applications/modern/conversion.json",
                        "distribution_contract": "applications/modern/openclaw/distribution.json",
                        "codex_destination": "plugins/modern",
                        "openclaw_destination": "openclaw/modern",
                        "mode": modern_mode,
                    },
                ],
            },
        )

    def _upgrade_to_v3(self, application: Path) -> None:
        contract_path = application / "openclaw" / "distribution.json"
        raw = json.loads(contract_path.read_text(encoding="utf-8"))
        (application / "docs").mkdir(exist_ok=True)
        (application / "docs" / "rights.md").write_text("approved\n", encoding="utf-8")
        raw.update(
            {
                "schema_version": 3,
                "include_prefixes": [],
                "rag": None,
                "content_rules": [
                    {
                        "id": "portable-text",
                        "paths": [".codex-plugin/plugin.json"],
                        "prefixes": [],
                        "classification": "text",
                        "redistribution": {
                            "status": "approved",
                            "provenance": "docs/rights.md",
                        },
                    }
                ],
                "publication": {
                    "github_marketplace": {"enabled": True},
                    "clawhub": {"enabled": False, "family": None, "native_manifest": None},
                },
            }
        )
        _write_json(contract_path, raw)

    def _add_codex_builder(self, application: Path) -> None:
        script = application / "scripts" / "build.py"
        script.parent.mkdir()
        script.write_text(
            "from pathlib import Path\n"
            "import json, sys\n"
            "root=Path(sys.argv[1])/'plugins'/'modern'\n"
            "(root/'.codex-plugin').mkdir(parents=True)\n"
            "(root/'.codex-plugin'/'plugin.json').write_text(json.dumps({'name':'modern','version':'1.2.3'}), encoding='utf-8')\n",
            encoding="utf-8",
        )
        data = self._conversion(application)
        data["verification"]["codex_build"]["argv"] = [  # type: ignore[index]
            "{python}", "-B", "{application_root}/scripts/build.py", "{diagnostics}/codex-marketplace"
        ]
        _write_json(application / "conversion.json", data)

    def _write_existing_legacy(self) -> None:
        codex = self.baseline / "plugins" / "legacy" / ".codex-plugin"
        codex.mkdir(parents=True)
        _write_json(codex / "plugin.json", {"name": "legacy", "version": "1.2.3"})
        package = self.baseline / "openclaw" / "legacy"
        package.mkdir(parents=True)
        payload = b"legacy\r\n"
        (package / "README.md").write_bytes(payload)
        records = [{"path": "README.md", "size": len(payload), "sha256": sha256(payload).hexdigest()}]
        identity = json.dumps(records, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        _write_json(
            package / "CONTENT-MANIFEST.json",
            {
                "schema_version": 1,
                "plugin_id": "legacy",
                "version": "1.2.3",
                "file_count": 1,
                "total_bytes": len(payload),
                "content_sha256": sha256(identity).hexdigest(),
                "files": records,
            },
        )

    def test_build_requires_v3_and_verify_existing_accepts_legacy(self) -> None:
        catalog = load_preparation_catalog(self.catalog_path, self.repository)
        self.assertEqual([entry.mode for entry in catalog.applications], ["verify_existing", "build"])

        self._write_catalog(modern_mode="verify_existing")
        raw = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        raw["applications"][0]["mode"] = "build"
        _write_json(self.catalog_path, raw)
        with self.assertRaisesRegex(MarketplaceError, "legacy_contract_read_only"):
            load_preparation_catalog(self.catalog_path, self.repository)

    def test_duplicate_destination_and_path_escape_are_rejected(self) -> None:
        raw = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        raw["applications"][1]["codex_destination"] = "plugins/legacy"
        _write_json(self.catalog_path, raw)
        with self.assertRaisesRegex(MarketplaceError, "duplicate_marketplace_destination"):
            load_preparation_catalog(self.catalog_path, self.repository)

        self._write_catalog()
        raw = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        raw["applications"][1]["application_config"] = "../escape.json"
        _write_json(self.catalog_path, raw)
        with self.assertRaisesRegex(MarketplaceError, "catalog_path_escape"):
            load_preparation_catalog(self.catalog_path, self.repository)

    def test_ancestor_and_descendant_destinations_are_rejected(self) -> None:
        raw = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        raw["applications"][1]["codex_destination"] = "plugins"
        _write_json(self.catalog_path, raw)

        with self.assertRaisesRegex(MarketplaceError, "overlapping_marketplace_destination"):
            load_preparation_catalog(self.catalog_path, self.repository)

    def test_windows_root_dot_and_case_equivalent_destinations_are_rejected(self) -> None:
        for unsafe in ("C:/outside-target", "C:\\outside-target", "."):
            with self.subTest(destination=unsafe):
                self._write_catalog()
                raw = json.loads(self.catalog_path.read_text(encoding="utf-8"))
                raw["applications"][1]["codex_destination"] = unsafe
                _write_json(self.catalog_path, raw)
                with self.assertRaisesRegex(MarketplaceError, "catalog_path_escape"):
                    load_preparation_catalog(self.catalog_path, self.repository)

        self._write_catalog()
        raw = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        raw["applications"][1]["codex_destination"] = "Plugins/Legacy"
        _write_json(self.catalog_path, raw)
        with self.assertRaisesRegex(MarketplaceError, "duplicate_marketplace_destination"):
            load_preparation_catalog(self.catalog_path, self.repository)

    def test_prepare_changes_only_declared_build_destinations_and_preserves_legacy(self) -> None:
        catalog = load_preparation_catalog(self.catalog_path, self.repository)
        baseline_before = self._tree(self.baseline)

        result = prepare_marketplace(catalog, self.baseline, self.output)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(self._tree(self.baseline), baseline_before)
        self.assertEqual((self.output / "untouched.txt").read_bytes(), b"untouched\r\n")
        self.assertEqual(
            self._tree(self.output / "plugins" / "legacy"),
            self._tree(self.baseline / "plugins" / "legacy"),
        )
        self.assertEqual(
            self._tree(self.output / "openclaw" / "legacy"),
            self._tree(self.baseline / "openclaw" / "legacy"),
        )
        self.assertTrue((self.output / "plugins/modern/.codex-plugin/plugin.json").is_file())
        self.assertTrue((self.output / "openclaw/modern/CONTENT-MANIFEST.json").is_file())

    def test_failed_product_audit_preserves_existing_output(self) -> None:
        hook = self.modern / "audit.py"
        hook.write_text("def audit(stage, contract):\n    return ['blocked']\n", encoding="utf-8")
        raw = json.loads((self.modern / "openclaw/distribution.json").read_text(encoding="utf-8"))
        raw["audit_hook"] = "audit.py:audit"
        _write_json(self.modern / "openclaw/distribution.json", raw)
        self.output.mkdir()
        (self.output / "keep.txt").write_text("keep", encoding="utf-8")
        catalog = load_preparation_catalog(self.catalog_path, self.repository)

        with self.assertRaisesRegex(ValueError, "product_audit_failed"):
            prepare_marketplace(catalog, self.baseline, self.output)

        self.assertEqual(self._tree(self.output), {"keep.txt": b"keep"})

    def test_unsafe_root_combinations_do_not_mutate(self) -> None:
        catalog = load_preparation_catalog(self.catalog_path, self.repository)
        cases = (
            (self.baseline, self.baseline),
            (self.baseline, self.baseline / "nested"),
            (self.baseline, self.repository),
            (self.repository, self.output),
            (self.baseline, self.modern),
            (self.baseline, self.modern / "openclaw"),
        )
        for baseline, output in cases:
            with self.subTest(baseline=baseline, output=output):
                before = self._tree(baseline) if baseline.is_dir() else {}
                with self.assertRaisesRegex(MarketplaceError, "unsafe_marketplace_path"):
                    prepare_marketplace(catalog, baseline, output)
                if baseline.is_dir():
                    self.assertEqual(self._tree(baseline), before)

    def test_generated_codex_artifact_is_checked_for_links_before_copy(self) -> None:
        catalog = load_preparation_catalog(self.catalog_path, self.repository)

        def reject_generated(root: Path) -> None:
            if root.name == "modern" and "codex-marketplace" in root.parts:
                raise MarketplaceError("link_forbidden", "outside-link")
            _reject_links(root)

        with patch(
            "obvious_one_plugin_framework.marketplace._reject_links",
            side_effect=reject_generated,
        ):
            with self.assertRaisesRegex(MarketplaceError, "link_forbidden"):
                prepare_marketplace(catalog, self.baseline, self.output)

        self.assertFalse(self.output.exists())

    def test_output_may_use_repository_owned_dist_root(self) -> None:
        catalog = load_preparation_catalog(self.catalog_path, self.repository)
        output = self.repository / "dist" / "marketplace"

        result = prepare_marketplace(catalog, self.baseline, output)

        self.assertEqual(result.status, "PASS")
        self.assertTrue((output / ".obvious-one-validation.json").is_file())

    def test_verify_existing_materializes_clean_committed_bytes_without_mutating_checkout(self) -> None:
        readme = self.baseline / "openclaw" / "legacy" / "README.md"
        payload = b"legacy\n"
        readme.write_bytes(payload)
        recorded_payload = b"legacy\n"
        records = [
            {
                "path": "README.md",
                "size": len(recorded_payload),
                "sha256": sha256(recorded_payload).hexdigest(),
            }
        ]
        identity = json.dumps(
            records, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode()
        _write_json(
            readme.parent / "CONTENT-MANIFEST.json",
            {
                "schema_version": 1,
                "plugin_id": "legacy",
                "version": "1.2.3",
                "file_count": 1,
                "total_bytes": len(recorded_payload),
                "content_sha256": sha256(identity).hexdigest(),
                "files": records,
            },
        )
        self.git(self.baseline, "init")
        self.git(self.baseline, "config", "user.email", "tests@example.invalid")
        self.git(self.baseline, "config", "user.name", "Framework Tests")
        self.git(self.baseline, "config", "core.autocrlf", "true")
        self.git(self.baseline, "add", ".")
        self.git(self.baseline, "commit", "-m", "baseline")
        readme.unlink()
        self.git(self.baseline, "checkout", "--", "openclaw/legacy/README.md")
        self.assertEqual(readme.read_bytes(), b"legacy\r\n")
        catalog = load_preparation_catalog(self.catalog_path, self.repository)

        result = prepare_marketplace(catalog, self.baseline, self.output)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(readme.read_bytes(), b"legacy\r\n")
        self.assertEqual(
            (self.output / "openclaw/legacy/README.md").read_bytes(), b"legacy\n"
        )
        self.assertFalse((self.output / ".git").exists())
        self.assertNotIn(
            "openclaw/legacy/README.md", result.evidence["changed_paths"]
        )

    def test_git_gate_runs_independently_when_product_verifier_fails(self) -> None:
        catalog = load_preparation_catalog(self.catalog_path, self.repository)
        prepared = prepare_marketplace(catalog, self.baseline, self.output)
        self.git(self.output, "init")
        self.git(self.output, "config", "user.email", "tests@example.invalid")
        self.git(self.output, "config", "user.name", "Framework Tests")
        self.git(self.output, "add", ".")
        clean = verify_marketplace(catalog, self.output, check_index=True)
        (self.output / "tools/verify_marketplace.py").write_text(
            "raise SystemExit(1)\n", encoding="utf-8", newline="\n"
        )

        result = verify_marketplace(catalog, self.output, check_index=True)

        self.assertEqual(clean.artifacts[0].sha256, prepared.artifacts[0].sha256)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.evidence["gates"]["filesystem"], "FAIL")
        self.assertEqual(result.evidence["gates"]["index"], "PASS")

    def test_zero_exit_tampered_verifier_and_registry_are_not_trusted(self) -> None:
        catalog = load_preparation_catalog(self.catalog_path, self.repository)
        prepare_marketplace(catalog, self.baseline, self.output)
        verifier = self.output / "tools/verify_marketplace.py"
        verifier.write_text("raise SystemExit(0)\n", encoding="utf-8")

        result = verify_marketplace(catalog, self.output)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.evidence["gates"]["filesystem"], "FAIL")

        prepare_marketplace(catalog, self.baseline, self.output)
        registry = self.output / ".obvious-one-validation.json"
        payload = json.loads(registry.read_text(encoding="utf-8"))
        payload["plugins"][0]["artifacts"]["codex"]["content_sha256"] = "0" * 64
        _write_json(registry, payload)
        result = verify_marketplace(catalog, self.output)
        self.assertEqual(result.status, "FAIL")

    def test_prepare_rejects_stale_legacy_manifest_before_replacement(self) -> None:
        manifest = self.baseline / "openclaw/legacy/CONTENT-MANIFEST.json"
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        payload["files"][0]["sha256"] = "0" * 64
        _write_json(manifest, payload)
        catalog = load_preparation_catalog(self.catalog_path, self.repository)

        with self.assertRaisesRegex(MarketplaceError, "content_manifest_mismatch"):
            prepare_marketplace(catalog, self.baseline, self.output)

        self.assertFalse(self.output.exists())

    def test_build_mode_updates_runtime_catalog_version_and_preserves_legacy(self) -> None:
        codex_catalog = self.baseline / ".agents/plugins/marketplace.json"
        openclaw_catalog = self.baseline / ".claude-plugin/marketplace.json"
        _write_json(codex_catalog, {"plugins": [
            {"name": "legacy", "source": {"path": "./plugins/legacy"}, "note": "keep"},
            {"name": "modern", "source": {"path": "./plugins/old"}},
        ]})
        _write_json(openclaw_catalog, {"plugins": [
            {"name": "legacy", "version": "1.2.3", "source": "./openclaw/legacy", "note": "keep"},
            {"name": "modern", "version": "1.2.2", "source": "./openclaw/old"},
        ]})
        catalog = load_preparation_catalog(self.catalog_path, self.repository)

        prepare_marketplace(catalog, self.baseline, self.output)

        codex = json.loads((self.output / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        openclaw = json.loads((self.output / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(codex["plugins"][0]["note"], "keep")
        self.assertEqual(codex["plugins"][1]["source"]["path"], "./plugins/modern")
        self.assertEqual(openclaw["plugins"][0]["note"], "keep")
        self.assertEqual(openclaw["plugins"][1]["version"], "1.2.3")
        self.assertEqual(openclaw["plugins"][1]["source"], "./openclaw/modern")

    def test_verifier_timeouts_are_isolated_per_plugin(self) -> None:
        catalog = load_preparation_catalog(self.catalog_path, self.repository)
        prepare_marketplace(catalog, self.baseline, self.output)

        with patch(
            "obvious_one_plugin_framework.marketplace.subprocess.run",
            side_effect=subprocess.TimeoutExpired(["verifier"], 180),
        ):
            result = verify_marketplace(catalog, self.output)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.evidence["gates"]["filesystem"], "FAIL")
        self.assertEqual(
            result.evidence["diagnostic_plugins"], ["legacy", "modern"]
        )

    @staticmethod
    def git(root: Path, *arguments: str) -> None:
        completed = subprocess.run(
            ["git", *arguments], cwd=root, capture_output=True, text=True, check=False
        )
        if completed.returncode:
            raise AssertionError(completed.stdout + completed.stderr)

    @staticmethod
    def _tree(root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }


if __name__ == "__main__":
    unittest.main()
