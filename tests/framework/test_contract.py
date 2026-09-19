from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from obvious_one_plugin_framework.contract import ContractError, load_contract


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ContractTests(unittest.TestCase):
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

if __name__ == "__main__":
    unittest.main()
