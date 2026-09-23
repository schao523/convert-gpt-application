from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from obvious_one_plugin_framework.contract import ContentRule, RedistributionEvidence, load_contract
from obvious_one_plugin_framework.package_builder import (
    PackageAuditError,
    build_package,
    preflight_package,
    verify_package,
)


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class PackageBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)

    def contract(self, name: str = "plugin-v3"):
        return load_contract(FIXTURES / name / "distribution.json")

    def native_contract(self):
        root = self.output / "native-contract"
        shutil.copytree(FIXTURES / "plugin-v3", root)
        source = root / "source"
        (source / "openclaw.plugin.json").write_text(
            json.dumps(
                {
                    "id": "plugin-v3",
                    "configSchema": {"type": "object", "additionalProperties": False},
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
        return load_contract(contract_path)

    def test_builder_vendors_bootstrap_into_each_plugin(self) -> None:
        result = build_package(self.contract(), self.output / "plugin-v3")
        bootstrap = result.output / "vendor/obvious-one-runtime/obvious_one_runtime/status.py"
        self.assertTrue(bootstrap.is_file())
        self.assertTrue((result.output / ".codex-plugin/plugin.json").is_file())
        self.assertFalse((result.output / "openclaw.plugin.json").exists())

    def test_skill_only_bundle_omits_unused_runtime_bootstrap(self) -> None:
        contract = replace(self.contract(), rag=None)

        result = build_package(contract, self.output / "skill-only")

        self.assertFalse((result.output / "vendor").exists())

    def test_repeat_build_has_identical_content_identity(self) -> None:
        one = build_package(self.contract(), self.output / "one")
        two = build_package(self.contract(), self.output / "two")
        self.assertEqual(one.content_sha256, two.content_sha256)
        self.assertEqual(
            (one.output / "CONTENT-MANIFEST.json").read_bytes(),
            (two.output / "CONTENT-MANIFEST.json").read_bytes(),
        )
        self.assertEqual(verify_package(self.contract(), one.output), one)

    def test_failed_audit_preserves_previous_output(self) -> None:
        contract = self.contract()
        target = self.output / "alpha"
        before = build_package(contract, target)
        source = self.output / "unsafe-source"
        shutil.copytree(contract.source_root, source)
        (source / "unsafe").mkdir()
        (source / "unsafe/.env").write_text("TOKEN=secret", encoding="utf-8")
        unsafe = replace(contract, source_root=source, include_prefixes=("unsafe",))
        unsafe = replace(
            unsafe,
            content_rules=unsafe.content_rules
            + (
                ContentRule(
                    "unsafe-text",
                    (),
                    ("unsafe",),
                    "text",
                    RedistributionEvidence("approved", "docs/source-decisions.md"),
                ),
            ),
        )
        with self.assertRaisesRegex(PackageAuditError, "forbidden_file"):
            build_package(unsafe, target)
        self.assertEqual(verify_package(contract, target).content_sha256, before.content_sha256)

    def test_package_json_uses_bundle_identity(self) -> None:
        result = build_package(self.contract(), self.output / "alpha")
        package = json.loads((result.output / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package["name"], "@obvious-one/plugin-v3")
        self.assertEqual(package["version"], "1.0.0")
        self.assertEqual(package["openclaw"]["family"], "bundle-plugin")
        self.assertNotIn("main", package)

    def test_native_clawhub_contract_builds_a_verifiable_native_artifact(self) -> None:
        contract = self.native_contract()

        result = build_package(contract, self.output / "native-package")
        package = json.loads((result.output / "package.json").read_text(encoding="utf-8"))

        self.assertTrue((result.output / "openclaw.plugin.json").is_file())
        self.assertTrue((result.output / "index.js").is_file())
        self.assertEqual(package["openclaw"]["extensions"], ["./index.js"])
        self.assertEqual(verify_package(contract, result.output), result)

    def test_declared_product_audit_hook_is_enforced(self) -> None:
        contract = self.contract()
        source = self.output / "hook-source"
        shutil.copytree(contract.source_root, source)
        (source / "audit_hook.py").write_text(
            "def audit(stage, contract):\n    raise ValueError('hook_seen')\n",
            encoding="utf-8",
        )
        hooked = replace(
            contract,
            source_root=source,
            audit_hook="audit_hook.py:audit",
        )
        with self.assertRaisesRegex(PackageAuditError, "product_audit_failed.*hook_seen"):
            build_package(hooked, self.output / "hooked")

    def test_legacy_build_is_rejected_before_output_parent_creation(self) -> None:
        legacy = load_contract(FIXTURES / "plugin-alpha" / "distribution.json")
        target = self.output / "missing-parent" / "legacy"

        with self.assertRaisesRegex(ValueError, "legacy_contract_read_only"):
            build_package(legacy, target)

        self.assertFalse(target.parent.exists())

    def test_schema_v3_manifest_records_content_policy(self) -> None:
        result = build_package(self.contract(), self.output / "plugin-v3")
        manifest = json.loads(
            (result.output / "CONTENT-MANIFEST.json").read_text(encoding="utf-8")
        )

        self.assertEqual(manifest["schema_version"], 2)
        records = {item["path"]: item for item in manifest["files"]}
        self.assertEqual(records["README.md"]["classification"], "text")
        self.assertEqual(records["README.md"]["canonicalization"], "utf8-lf")
        self.assertEqual(records["assets/logo.bin"]["classification"], "binary")
        self.assertEqual(records["assets/logo.bin"]["canonicalization"], "exact")
        self.assertEqual(records["package.json"]["classification"], "generated-json")

    def test_policy_failure_does_not_create_output_parent(self) -> None:
        contract = self.contract()
        source = self.output / "unclassified-source"
        shutil.copytree(contract.source_root, source)
        (source / "new.txt").write_text("owner decision required\n", encoding="utf-8")
        unclassified = replace(
            contract,
            source_root=source,
            include_files=contract.include_files + ("new.txt",),
        )
        target = self.output / "not-created" / "plugin"

        with self.assertRaisesRegex(ValueError, "unclassified_files"):
            build_package(unclassified, target)

        self.assertFalse(target.parent.exists())

    def test_selected_file_rejects_linked_parent_component(self) -> None:
        contract = self.contract()
        source = self.output / "linked-source"
        shutil.copytree(contract.source_root, source)
        (source / "linked").mkdir()
        (source / "linked/file.txt").write_text("outside\n", encoding="utf-8")
        linked = replace(
            contract,
            source_root=source,
            include_files=contract.include_files + ("linked/file.txt",),
            content_rules=contract.content_rules + (
                ContentRule(
                    "linked-text", ("linked/file.txt",), (), "text",
                    RedistributionEvidence("approved", "docs/source-decisions.md"),
                ),
            ),
        )
        original = __import__(
            "obvious_one_plugin_framework.package_builder", fromlist=["_is_reparse_or_symlink"]
        )._is_reparse_or_symlink

        with patch(
            "obvious_one_plugin_framework.package_builder._is_reparse_or_symlink",
            side_effect=lambda path: path.name == "linked" or original(path),
        ):
            with self.assertRaisesRegex(PackageAuditError, "link_forbidden"):
                preflight_package(linked)

    def test_application_paths_cannot_collide_with_generated_outputs(self) -> None:
        contract = self.contract()
        source = self.output / "collision-source"
        shutil.copytree(contract.source_root, source)
        (source / "Package.json").write_text("{}\n", encoding="utf-8")
        collision = replace(
            contract,
            source_root=source,
            include_files=contract.include_files + ("Package.json",),
            content_rules=contract.content_rules + (
                ContentRule(
                    "collision", ("Package.json",), (), "text",
                    RedistributionEvidence("approved", "docs/source-decisions.md"),
                ),
            ),
        )

        with self.assertRaisesRegex(PackageAuditError, "reserved_path_collision"):
            build_package(collision, self.output / "collision-output")

    def test_legacy_manifest_remains_verifiable_without_rebuild(self) -> None:
        contract = load_contract(FIXTURES / "plugin-alpha" / "distribution.json")
        output = self.output / "legacy-existing"
        output.mkdir()
        payload = b"legacy bytes\r\n"
        (output / "README.md").write_bytes(payload)
        records = [
            {
                "path": "README.md",
                "size": len(payload),
                "sha256": sha256(payload).hexdigest(),
            }
        ]
        identity = json.dumps(
            records, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        manifest = {
            "schema_version": 1,
            "plugin_id": contract.plugin_id,
            "version": contract.version,
            "file_count": 1,
            "total_bytes": len(payload),
            "content_sha256": sha256(identity).hexdigest(),
            "files": records,
        }
        (output / "CONTENT-MANIFEST.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )

        result = verify_package(contract, output)

        self.assertEqual(result.content_sha256, manifest["content_sha256"])


if __name__ == "__main__":
    unittest.main()
