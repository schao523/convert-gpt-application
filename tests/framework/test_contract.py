from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from obvious_one_plugin_framework.contract import (
    ContractError,
    load_contract,
    require_buildable_contract,
)


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ContractTests(unittest.TestCase):
    def test_schema_v3_loads_content_and_publication_rules(self) -> None:
        contract = load_contract(FIXTURES / "plugin-v3" / "distribution.json")

        self.assertEqual(contract.schema_version, 3)
        self.assertEqual(contract.content_rules[0].classification, "text")
        self.assertTrue(contract.publication.github_marketplace.enabled)
        self.assertFalse(contract.publication.clawhub.enabled)

    def test_legacy_contract_is_read_only_for_builds(self) -> None:
        contract = load_contract(FIXTURES / "plugin-alpha" / "distribution.json")

        with self.assertRaisesRegex(ContractError, "legacy_contract_read_only"):
            require_buildable_contract(contract)

    def test_schema_v3_rejects_unknown_keys(self) -> None:
        with self.assertRaisesRegex(ContractError, "unknown_key"):
            self._load_modified_v3(lambda raw: raw.update({"surprise": True}))

    def test_schema_v3_rejects_empty_rule_selectors(self) -> None:
        def modify(raw: dict[str, object]) -> None:
            raw["content_rules"][0]["paths"] = []
            raw["content_rules"][0]["prefixes"] = []

        with self.assertRaisesRegex(ContractError, "empty_rule_selector"):
            self._load_modified_v3(modify)

    def test_schema_v3_rejects_duplicate_rule_ids(self) -> None:
        def modify(raw: dict[str, object]) -> None:
            raw["content_rules"].append(dict(raw["content_rules"][0]))

        with self.assertRaisesRegex(ContractError, "duplicate_content_rule"):
            self._load_modified_v3(modify)

    def test_schema_v3_rejects_unsafe_provenance_paths(self) -> None:
        def modify(raw: dict[str, object]) -> None:
            raw["content_rules"][0]["redistribution"]["provenance"] = "../private.md"

        with self.assertRaisesRegex(ContractError, "asset_path_escape"):
            self._load_modified_v3(modify)

    def test_schema_v3_rejects_disabled_clawhub_fields(self) -> None:
        def modify(raw: dict[str, object]) -> None:
            raw["publication"]["clawhub"]["family"] = "native-plugin"

        with self.assertRaisesRegex(ContractError, "clawhub_disabled_fields"):
            self._load_modified_v3(modify)

    def test_schema_v3_rejects_enabled_clawhub_without_native_manifest(self) -> None:
        def modify(raw: dict[str, object]) -> None:
            raw["publication"]["clawhub"].update(
                {"enabled": True, "family": "native-plugin", "native_manifest": None}
            )

        with self.assertRaisesRegex(ContractError, "clawhub_native_manifest_required"):
            self._load_modified_v3(modify)

    def test_schema_v3_rejects_incompatible_clawhub_native_manifest(self) -> None:
        def modify(raw: dict[str, object]) -> None:
            raw["publication"]["clawhub"].update(
                {
                    "enabled": True,
                    "family": "native-plugin",
                    "native_manifest": "README.md",
                }
            )

        with self.assertRaisesRegex(ContractError, "clawhub_native_manifest_invalid"):
            self._load_modified_v3(modify)

    def test_schema_v3_accepts_complete_native_clawhub_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin-v3"
            shutil.copytree(FIXTURES / "plugin-v3", root)
            source = root / "source"
            (source / "openclaw.plugin.json").write_text(
                json.dumps(
                    {
                        "id": "plugin-v3",
                        "configSchema": {
                            "type": "object",
                            "additionalProperties": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            (source / "index.js").write_text("export default {};\n", encoding="utf-8")
            (source / "package.json").write_text(
                json.dumps(
                    {
                        "name": "@obvious-one/plugin-v3",
                        "version": "1.0.0",
                        "openclaw": {"extensions": ["./index.js"]},
                    }
                ),
                encoding="utf-8",
            )
            contract_path = root / "distribution.json"
            raw = json.loads(contract_path.read_text(encoding="utf-8"))
            raw["publication"]["clawhub"].update(
                {
                    "enabled": True,
                    "family": "native-plugin",
                    "native_manifest": "openclaw.plugin.json",
                }
            )
            contract_path.write_text(json.dumps(raw), encoding="utf-8")

            contract = load_contract(contract_path)

            self.assertTrue(contract.publication.clawhub.enabled)

    def test_schema_v3_rejects_missing_provenance_file(self) -> None:
        def modify(raw: dict[str, object]) -> None:
            raw["content_rules"][0]["redistribution"]["provenance"] = "docs/missing.md"

        with self.assertRaisesRegex(ContractError, "rights_unresolved"):
            self._load_modified_v3(modify)

    def test_schema_v2_accepts_skill_only_contract_without_rag(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            manifest = source / ".codex-plugin" / "plugin.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                json.dumps({"name": "skill-only", "version": "1.0.0"}),
                encoding="utf-8",
            )
            (source / "README.md").write_text("skill only\n", encoding="utf-8")
            contract_path = root / "distribution.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "plugin_id": "skill-only",
                        "package_name": "@obvious-one/skill-only",
                        "family": "bundle-plugin",
                        "version": "1.0.0",
                        "source_root": "source",
                        "include_files": ["README.md", ".codex-plugin/plugin.json"],
                        "include_prefixes": [],
                        "exclude_paths": [],
                        "max_total_bytes": 1048576,
                        "release_repository": "example/plugins",
                        "release_tag_template": "skill-only-v{version}",
                        "readme_overlay": None,
                        "audit_hook": None,
                        "rag": None,
                    }
                ),
                encoding="utf-8",
            )

            contract = load_contract(contract_path)

            self.assertIsNone(contract.rag)

    def test_two_plugins_keep_distinct_content_identity(self) -> None:
        alpha = load_contract(FIXTURES / "plugin-alpha" / "distribution.json")
        beta = load_contract(FIXTURES / "plugin-beta" / "distribution.json")
        self.assertEqual(alpha.rag.runtime_lock_digest, beta.rag.runtime_lock_digest)
        self.assertEqual(alpha.rag.model_digest, beta.rag.model_digest)
        self.assertNotEqual(alpha.plugin_id, beta.plugin_id)
        self.assertNotEqual(alpha.rag.app_id, beta.rag.app_id)
        self.assertNotEqual(alpha.rag.namespace, beta.rag.namespace)

    def test_contract_rejects_asset_path_escape(self) -> None:
        raw = self._raw_alpha()
        raw["rag"]["asset_groups"][0]["install_subdir"] = "../../shared-rag/indexes"
        with patch.object(Path, "read_text", return_value=json.dumps(raw)):
            with self.assertRaisesRegex(ContractError, "asset_path_escape"):
                load_contract(FIXTURES / "plugin-alpha" / "distribution.json")

    def test_contract_rejects_namespace_not_owned_by_app(self) -> None:
        raw = self._raw_alpha()
        raw["rag"]["namespace"] = "plugin-beta:docs"
        with patch.object(Path, "read_text", return_value=json.dumps(raw)):
            with self.assertRaisesRegex(ContractError, "namespace_owner_mismatch"):
                load_contract(FIXTURES / "plugin-alpha" / "distribution.json")

    def test_contract_rejects_unknown_key(self) -> None:
        raw = self._raw_alpha()
        raw["surprise"] = True
        with patch.object(Path, "read_text", return_value=json.dumps(raw)):
            with self.assertRaisesRegex(ContractError, "unknown_key"):
                load_contract(FIXTURES / "plugin-alpha" / "distribution.json")

    def _raw_alpha(self) -> dict[str, object]:
        path = FIXTURES / "plugin-alpha" / "distribution.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def _load_modified_v3(self, modify) -> object:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin-v3"
            shutil.copytree(FIXTURES / "plugin-v3", root)
            contract_path = root / "distribution.json"
            raw = json.loads(contract_path.read_text(encoding="utf-8"))
            modify(raw)
            contract_path.write_text(json.dumps(raw), encoding="utf-8")
            return load_contract(contract_path)

if __name__ == "__main__":
    unittest.main()
