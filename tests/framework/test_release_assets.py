from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
import zipfile

from obvious_one_plugin_framework.contract import AssetGroup, load_contract
from obvious_one_plugin_framework.release_assets import (
    AssetBuildError,
    build_asset_groups,
    remote_manifest_data,
)


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ReleaseAssetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)

    def contract(self):
        return load_contract(FIXTURES / "plugin-alpha" / "distribution.json")

    def test_asset_archives_are_owned_and_byte_reproducible(self) -> None:
        records_a = build_asset_groups(self.contract(), self.output / "a")
        records_b = build_asset_groups(self.contract(), self.output / "b")
        self.assertEqual(records_a, records_b)
        self.assertTrue(all(item.owner_plugin_id == "plugin-alpha" for item in records_a))
        for record in records_a:
            self.assertEqual(
                (self.output / "a" / record.name).read_bytes(),
                (self.output / "b" / record.name).read_bytes(),
            )
            with zipfile.ZipFile(self.output / "a" / record.name) as archive:
                self.assertTrue(
                    all(member.create_system == 0 for member in archive.infolist())
                )
                self.assertTrue(
                    all(
                        member.compress_type == zipfile.ZIP_STORED
                        for member in archive.infolist()
                    )
                )

    def test_asset_source_cannot_escape_plugin_root(self) -> None:
        contract = self.contract()
        escaped = AssetGroup(
            name="escaped",
            archive_name="escaped-{version}.zip",
            source_paths=("../plugin-beta/source/assets/index.bin",),
            install_subdir="indexes",
        )
        unsafe = replace(contract, rag=replace(contract.rag, asset_groups=(escaped,)))
        with self.assertRaisesRegex(AssetBuildError, "source_path_escape"):
            build_asset_groups(unsafe, self.output / "unsafe")

    def test_remote_manifest_has_immutable_owner_and_release_tag(self) -> None:
        records = build_asset_groups(self.contract(), self.output / "assets")
        manifest = remote_manifest_data(self.contract(), records)
        self.assertEqual(manifest["plugin_id"], "plugin-alpha")
        self.assertEqual(manifest["release_tag"], "plugin-alpha-v1.0.0")
        self.assertEqual(
            {item["owner_plugin_id"] for item in manifest["asset_groups"]},
            {"plugin-alpha"},
        )
        self.assertTrue(
            all("/releases/download/plugin-alpha-v1.0.0/" in item["url"] for item in manifest["asset_groups"])
        )


if __name__ == "__main__":
    unittest.main()
