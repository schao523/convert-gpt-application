from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from tests.framework.test_verification_config import _make_application, _write_json

from obvious_one_plugin_framework.marketplace import (
    MarketplaceError,
    load_preparation_catalog,
    prepare_marketplace,
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
        )
        for baseline, output in cases:
            with self.subTest(baseline=baseline, output=output):
                before = self._tree(baseline) if baseline.is_dir() else {}
                with self.assertRaisesRegex(MarketplaceError, "unsafe_marketplace_path"):
                    prepare_marketplace(catalog, baseline, output)
                if baseline.is_dir():
                    self.assertEqual(self._tree(baseline), before)

    @staticmethod
    def _tree(root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }


if __name__ == "__main__":
    unittest.main()
